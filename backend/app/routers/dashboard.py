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
