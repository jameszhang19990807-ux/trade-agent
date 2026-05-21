"""
Price Library — product matching and pricing lookup service.
"""
from dataclasses import dataclass
from typing import Optional
import json

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.product import Product, PricingTier
from ..config import settings


@dataclass
class PriceResult:
    found: bool
    product: Optional[dict] = None
    matched_tier: Optional[dict] = None
    all_tiers: list = None
    message: str = ""


class PriceLibrary:
    def __init__(self):
        self._cache = {}  # Simple in-memory cache; replace with Redis in production

    async def lookup(
        self,
        db: AsyncSession,
        product_query: Optional[str] = None,
        quantity: Optional[int] = None,
        customer_id: Optional[int] = None,
    ) -> PriceResult:
        if not product_query:
            return PriceResult(found=False, message="No product query provided")

        # Try exact SKU match first
        product = await self._find_product(db, product_query)
        if not product:
            return PriceResult(found=False, message=f"No product found for: {product_query}")

        # Load pricing tiers
        await db.refresh(product, ["pricing_tiers"])
        tiers = sorted(product.pricing_tiers, key=lambda t: t.quantity_min)

        if not tiers:
            return PriceResult(
                found=True,
                product=self._product_to_dict(product),
                message="Product found but no pricing configured",
            )

        # Match quantity to a tier
        matched_tier = None
        qty = quantity or 0
        for tier in tiers:
            if tier.quantity_min <= qty <= tier.quantity_max:
                matched_tier = tier
                break

        if not matched_tier and qty > 0:
            # Quantity above all tiers — use the highest tier
            matched_tier = tiers[-1]

        return PriceResult(
            found=True,
            product=self._product_to_dict(product),
            matched_tier=self._tier_to_dict(matched_tier) if matched_tier else None,
            all_tiers=[self._tier_to_dict(t) for t in tiers],
            message="OK",
        )

    async def _find_product(self, db: AsyncSession, query: str) -> Optional[Product]:
        # Exact SKU match
        result = await db.execute(
            select(Product).where(Product.sku == query.strip().upper())
        )
        product = result.scalar_one_or_none()
        if product:
            return product

        # Fuzzy match on name (contains search)
        pattern = f"%{query.strip()}%"
        result = await db.execute(
            select(Product).where(
                or_(
                    Product.name_en.ilike(pattern),
                    Product.name_cn.ilike(pattern),
                    Product.sku.ilike(pattern),
                )
            ).limit(5)
        )
        products = result.scalars().all()
        return products[0] if products else None

    def _product_to_dict(self, p: Product) -> dict:
        return {
            "id": p.id,
            "sku": p.sku,
            "name_en": p.name_en,
            "name_cn": p.name_cn,
            "description": p.description,
            "specs": p.specs,
            "moq": p.moq,
            "lead_time_days": p.lead_time_days,
        }

    def _tier_to_dict(self, t: PricingTier) -> dict:
        return {
            "tier_name": t.tier_name,
            "quantity_min": t.quantity_min,
            "quantity_max": t.quantity_max,
            "unit_price": t.unit_price,
            "currency": t.currency,
            "fob_price": t.fob_price,
            "cif_price": t.cif_price,
        }


price_library = PriceLibrary()
