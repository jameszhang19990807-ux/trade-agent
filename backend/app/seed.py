"""
Seed demo data for development and testing.
Run: python -m app.seed
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings
from .models.base import Base
from .models.product import Product, PricingTier, ProductCategory
from .models.customer import Customer
from .models.conversation import Conversation, Message


DEMO_PRODUCTS = [
    {
        "sku": "SP-450-144",
        "name_en": "Mono Solar Panel 450W",
        "name_cn": "单晶太阳能板 450W",
        "category": "Solar Panel",
        "description": "High-efficiency monocrystalline solar panel, 144 half-cells, PERC technology.",
        "specs": {"power": "450W", "cell_type": "Monocrystalline", "cells": "144", "efficiency": "21.5%", "weight": "24kg"},
        "moq": 50,
        "lead_time_days": 15,
        "tiers": [
            ("样品", 1, 10, 110, 100),
            ("小批", 50, 200, 85, 78),
            ("中批", 200, 1000, 72, 68),
            ("大批", 1000, 10000, 62, 58),
        ],
    },
    {
        "sku": "SP-550-144",
        "name_en": "Mono Solar Panel 550W",
        "name_cn": "单晶太阳能板 550W",
        "category": "Solar Panel",
        "description": "High-power monocrystalline solar panel, bifacial option available.",
        "specs": {"power": "550W", "cell_type": "Monocrystalline", "cells": "144", "efficiency": "22.8%", "weight": "28kg"},
        "moq": 50,
        "lead_time_days": 20,
        "tiers": [
            ("样品", 1, 10, 135, 125),
            ("小批", 50, 200, 102, 95),
            ("中批", 200, 1000, 88, 82),
            ("大批", 1000, 10000, 75, 70),
        ],
    },
    {
        "sku": "INV-5KW-48",
        "name_en": "Hybrid Inverter 5KW 48V",
        "name_cn": "混合逆变器 5KW 48V",
        "category": "Inverter",
        "description": "Off-grid hybrid solar inverter with MPPT charger, pure sine wave.",
        "specs": {"power": "5KW", "voltage": "48V", "type": "Hybrid", "mppt": "Built-in", "waveform": "Pure Sine"},
        "moq": 10,
        "lead_time_days": 10,
        "tiers": [
            ("样品", 1, 5, 520, 500),
            ("小批", 10, 100, 380, 365),
            ("中批", 100, 500, 320, 310),
            ("大批", 500, 5000, 280, 270),
        ],
    },
    {
        "sku": "BAT-5KWH-LFP",
        "name_en": "Lithium Battery 5KWh 48V LiFePO4",
        "name_cn": "锂电池 5KWh 48V 磷酸铁锂",
        "category": "Battery",
        "description": "Wall-mounted LiFePO4 battery, 6000+ cycles, BMS included.",
        "specs": {"capacity": "5KWh", "voltage": "48V", "chemistry": "LiFePO4", "cycles": "6000+", "bms": "Built-in"},
        "moq": 5,
        "lead_time_days": 12,
        "tiers": [
            ("样品", 1, 5, 950, 920),
            ("小批", 5, 50, 780, 760),
            ("中批", 50, 200, 680, 665),
            ("大批", 200, 2000, 590, 580),
        ],
    },
    {
        "sku": "LED-FL-200W",
        "name_en": "LED Flood Light 200W",
        "name_cn": "LED投光灯 200W",
        "category": "LED Lighting",
        "description": "Outdoor LED floodlight, IP66 waterproof, 50000h lifespan.",
        "specs": {"power": "200W", "ip_rating": "IP66", "lifespan": "50000h", "chip": "SMD3030", "cct": "3000-6500K"},
        "moq": 20,
        "lead_time_days": 7,
        "tiers": [
            ("样品", 1, 5, 45, 42),
            ("小批", 20, 200, 28, 26),
            ("中批", 200, 1000, 22, 21),
            ("大批", 1000, 10000, 18, 17),
        ],
    },
]

DEMO_CUSTOMERS = [
    {"whatsapp_number": "2348012345678", "name": "Emeka Okafor", "company_name": "GreenPower Nigeria Ltd", "country": "Nigeria", "language": "en", "pipeline_stage": "deep_talk"},
    {"whatsapp_number": "971501234567", "name": "Ahmed Al-Rashid", "company_name": "Dubai Solar Trading", "country": "UAE", "language": "en", "pipeline_stage": "sample_trial"},
    {"whatsapp_number": "5511998765432", "name": "Carlos Silva", "company_name": "Energia Brasil Imports", "country": "Brazil", "language": "pt", "pipeline_stage": "replied"},
    {"whatsapp_number": "212612345678", "name": "Youssef Benali", "company_name": "Sahara Energy Solutions", "country": "Morocco", "language": "fr", "pipeline_stage": "new_lead"},
]


async def seed():
    engine = create_async_engine(settings.async_database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Check if already seeded
        result = await db.execute(select(Product).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        # Create categories
        categories = {}
        cat_names = {"Solar Panel": "太阳能板", "Inverter": "逆变器", "Battery": "电池", "LED Lighting": "LED照明"}
        for name_en, name_cn in cat_names.items():
            cat = ProductCategory(name_en=name_en, name_cn=name_cn)
            db.add(cat)
            categories[name_en] = cat
        await db.flush()

        # Create products with pricing tiers
        for pdata in DEMO_PRODUCTS:
            product = Product(
                sku=pdata["sku"],
                name_en=pdata["name_en"],
                name_cn=pdata["name_cn"],
                category_id=categories[pdata["category"]].id,
                description=pdata["description"],
                specs=pdata["specs"],
                moq=pdata["moq"],
                lead_time_days=pdata["lead_time_days"],
            )
            db.add(product)
            await db.flush()

            for tier_name, qmin, qmax, unit_price, fob_price in pdata["tiers"]:
                tier = PricingTier(
                    product_id=product.id,
                    tier_name=tier_name,
                    quantity_min=qmin,
                    quantity_max=qmax,
                    unit_price=unit_price,
                    fob_price=fob_price,
                )
                db.add(tier)

        # Create demo customers
        for cdata in DEMO_CUSTOMERS:
            customer = Customer(**cdata)
            db.add(customer)

        await db.commit()
        print(f"Seeded {len(DEMO_PRODUCTS)} products and {len(DEMO_CUSTOMERS)} customers.")


if __name__ == "__main__":
    asyncio.run(seed())
