"""
Dashboard API — pipeline overview, conversation list, customer management.
"""
from fastapi import APIRouter, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, desc
from sqlalchemy.orm import selectinload

from ..models.customer import Customer
from ..models.conversation import Conversation, Message

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/overview")
async def dashboard_overview(request: Request):
    db: AsyncSession = request.state.db

    # Pipeline stats
    pipeline_result = await db.execute(
        select(Customer.pipeline_stage, func.count(Customer.id))
        .group_by(Customer.pipeline_stage)
    )
    pipeline = [{"stage": row[0], "count": row[1]} for row in pipeline_result.fetchall()]

    total_leads = sum(p["count"] for p in pipeline)
    total_conversations_result = await db.execute(select(func.count(Conversation.id)))
    total_conversations = total_conversations_result.scalar()

    # Auto-reply rate
    auto_msgs_result = await db.execute(
        select(func.count(Message.id)).where(Message.is_auto_generated == True)
    )
    auto_msgs = auto_msgs_result.scalar() or 0
    total_msgs_result = await db.execute(
        select(func.count(Message.id)).where(Message.direction == "outbound")
    )
    total_outbound = total_msgs_result.scalar() or 1
    auto_reply_rate = round(auto_msgs / total_outbound * 100, 1)

    # Conversion rate
    won_result = await db.execute(
        select(func.count(Customer.id)).where(Customer.pipeline_stage == "won")
    )
    won = won_result.scalar() or 0
    conversion_rate = round(won / max(total_leads, 1) * 100, 1)

    # Recent conversations
    recent_result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.customer), selectinload(Conversation.messages))
        .order_by(desc(Conversation.updated_at))
        .limit(20)
    )
    recent_convos = recent_result.scalars().all()

    recent_list = []
    for c in recent_convos:
        last_msg = c.messages[-1].content if c.messages else ""
        recent_list.append({
            "id": c.id,
            "customer_id": c.customer_id,
            "customer_name": c.customer.display_name if c.customer else "Unknown",
            "status": c.status,
            "is_human_handling": c.is_human_handling,
            "intent_code": c.intent_code,
            "auto_round_count": c.auto_round_count,
            "last_message_preview": last_msg[:100] if last_msg else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })

    return {
        "total_leads": total_leads,
        "total_conversations": total_conversations,
        "auto_reply_rate": auto_reply_rate,
        "conversion_rate": conversion_rate,
        "pipeline": pipeline,
        "recent_conversations": recent_list,
    }


@router.get("/customers")
async def list_customers(
    request: Request,
    stage: str = Query(default=None),
    country: str = Query(default=None),
    limit: int = Query(default=50),
    offset: int = Query(default=0),
):
    db: AsyncSession = request.state.db
    q = select(Customer)
    if stage:
        q = q.where(Customer.pipeline_stage == stage)
    if country:
        q = q.where(Customer.country == country)
    q = q.order_by(desc(Customer.last_contact_at)).offset(offset).limit(limit)
    result = await db.execute(q)
    customers = result.scalars().all()
    return {"customers": [{
        "id": c.id,
        "whatsapp_number": c.whatsapp_number[-4:].rjust(len(c.whatsapp_number), "*"),
        "name": c.display_name,
        "country": c.country,
        "pipeline_stage": c.pipeline_stage,
        "total_inquiries": c.total_inquiries,
        "total_orders": c.total_orders,
        "total_value_usd": c.total_value_usd,
        "last_contact_at": c.last_contact_at.isoformat() if c.last_contact_at else None,
    } for c in customers]}


@router.get("/conversations/{conversation_id}")
async def get_conversation(request: Request, conversation_id: int):
    db: AsyncSession = request.state.db
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages), selectinload(Conversation.customer))
        .where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        return {"error": "Not found"}

    return {
        "id": conv.id,
        "customer": {
            "id": conv.customer.id,
            "name": conv.customer.display_name,
            "country": conv.customer.country,
            "pipeline_stage": conv.customer.pipeline_stage,
        },
        "status": conv.status,
        "is_human_handling": conv.is_human_handling,
        "intent_code": conv.intent_code,
        "messages": [{
            "id": m.id,
            "direction": m.direction,
            "sender_name": m.sender_name,
            "content": m.content,
            "is_auto_generated": m.is_auto_generated,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        } for m in conv.messages],
    }


@router.post("/conversations/{conversation_id}/takeover")
async def takeover_conversation(request: Request, conversation_id: int):
    """Human agent takes over a conversation."""
    db: AsyncSession = request.state.db
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if not conv:
        return {"error": "Not found"}

    conv.is_human_handling = True
    conv.status = "human_takeover"
    await db.commit()
    return {"status": "ok", "message": "Human takeover confirmed"}


@router.post("/customers/{customer_id}/stage")
async def update_pipeline_stage(request: Request, customer_id: int, stage: str = Query(...)):
    """Move customer to a different pipeline stage."""
    db: AsyncSession = request.state.db
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        return {"error": "Not found"}

    valid_stages = ["new_lead", "replied", "deep_talk", "sample_trial", "formal_order", "won", "lost", "dormant"]
    if stage not in valid_stages:
        return {"error": f"Invalid stage. Valid: {valid_stages}"}

    customer.pipeline_stage = stage
    await db.commit()
    return {"status": "ok", "customer_id": customer_id, "new_stage": stage}


@router.post("/seed")
async def seed_demo_data(request: Request):
    """Seed demo products and customers (idempotent)."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from ..models.product import Product, PricingTier, ProductCategory
    from ..models.customer import Customer
    from sqlalchemy import select

    db: AsyncSession = request.state.db

    result = await db.execute(select(Product).limit(1))
    if result.scalar_one_or_none():
        return {"status": "skipped", "message": "Already seeded"}

    DEMO_PRODUCTS = [
        {"sku": "SP-450-144", "name_en": "Mono Solar Panel 450W", "name_cn": "单晶太阳能板 450W", "category": "Solar Panel", "description": "High-efficiency monocrystalline solar panel, 144 half-cells, PERC technology.", "specs": {"power": "450W", "cell_type": "Monocrystalline", "cells": "144", "efficiency": "21.5%"}, "moq": 50, "lead_time_days": 15, "tiers": [("样品", 1, 10, 110, 100), ("小批", 50, 200, 85, 78), ("中批", 200, 1000, 72, 68), ("大批", 1000, 10000, 62, 58)]},
        {"sku": "SP-550-144", "name_en": "Mono Solar Panel 550W", "name_cn": "单晶太阳能板 550W", "category": "Solar Panel", "description": "High-power monocrystalline solar panel, bifacial option available.", "specs": {"power": "550W", "cell_type": "Monocrystalline", "cells": "144", "efficiency": "22.8%"}, "moq": 50, "lead_time_days": 20, "tiers": [("样品", 1, 10, 135, 125), ("小批", 50, 200, 102, 95), ("中批", 200, 1000, 88, 82), ("大批", 1000, 10000, 75, 70)]},
        {"sku": "INV-5KW-48", "name_en": "Hybrid Inverter 5KW 48V", "name_cn": "混合逆变器 5KW 48V", "category": "Inverter", "description": "Off-grid hybrid solar inverter with MPPT charger, pure sine wave.", "specs": {"power": "5KW", "voltage": "48V", "type": "Hybrid"}, "moq": 10, "lead_time_days": 10, "tiers": [("样品", 1, 5, 520, 500), ("小批", 10, 100, 380, 365), ("中批", 100, 500, 320, 310), ("大批", 500, 5000, 280, 270)]},
        {"sku": "BAT-5KWH-LFP", "name_en": "Lithium Battery 5KWh 48V", "name_cn": "锂电池 5KWh 48V 磷酸铁锂", "category": "Battery", "description": "Wall-mounted LiFePO4 battery, 6000+ cycles, BMS included.", "specs": {"capacity": "5KWh", "voltage": "48V", "chemistry": "LiFePO4", "cycles": "6000+"}, "moq": 5, "lead_time_days": 12, "tiers": [("样品", 1, 5, 950, 920), ("小批", 5, 50, 780, 760), ("中批", 50, 200, 680, 665), ("大批", 200, 2000, 590, 580)]},
        {"sku": "LED-FL-200W", "name_en": "LED Flood Light 200W", "name_cn": "LED投光灯 200W", "category": "LED Lighting", "description": "Outdoor LED floodlight, IP66 waterproof, 50000h lifespan.", "specs": {"power": "200W", "ip_rating": "IP66", "lifespan": "50000h"}, "moq": 20, "lead_time_days": 7, "tiers": [("样品", 1, 5, 45, 42), ("小批", 20, 200, 28, 26), ("中批", 200, 1000, 22, 21), ("大批", 1000, 10000, 18, 17)]},
    ]

    DEMO_CUSTOMERS = [
        {"whatsapp_number": "2348012345678", "name": "Emeka Okafor", "company_name": "GreenPower Nigeria Ltd", "country": "Nigeria", "language": "en", "pipeline_stage": "deep_talk"},
        {"whatsapp_number": "971501234567", "name": "Ahmed Al-Rashid", "company_name": "Dubai Solar Trading", "country": "UAE", "language": "en", "pipeline_stage": "sample_trial"},
        {"whatsapp_number": "5511998765432", "name": "Carlos Silva", "company_name": "Energia Brasil Imports", "country": "Brazil", "language": "pt", "pipeline_stage": "replied"},
        {"whatsapp_number": "212612345678", "name": "Youssef Benali", "company_name": "Sahara Energy Solutions", "country": "Morocco", "language": "fr", "pipeline_stage": "new_lead"},
    ]

    cat_map = {}
    for name_en in ["Solar Panel", "Inverter", "Battery", "LED Lighting"]:
        cat = ProductCategory(name_en=name_en, name_cn={"Solar Panel": "太阳能板", "Inverter": "逆变器", "Battery": "电池", "LED Lighting": "LED照明"}[name_en])
        db.add(cat)
        cat_map[name_en] = cat
    await db.flush()

    for p in DEMO_PRODUCTS:
        product = Product(sku=p["sku"], name_en=p["name_en"], name_cn=p["name_cn"], category_id=cat_map[p["category"]].id, description=p["description"], specs=p["specs"], moq=p["moq"], lead_time_days=p["lead_time_days"])
        db.add(product)
        await db.flush()
        for tier_name, qmin, qmax, unit_price, fob_price in p["tiers"]:
            db.add(PricingTier(product_id=product.id, tier_name=tier_name, quantity_min=qmin, quantity_max=qmax, unit_price=unit_price, fob_price=fob_price))

    for c in DEMO_CUSTOMERS:
        db.add(Customer(**c))

    await db.commit()
    return {"status": "ok", "message": f"Seeded {len(DEMO_PRODUCTS)} products and {len(DEMO_CUSTOMERS)} customers"}
