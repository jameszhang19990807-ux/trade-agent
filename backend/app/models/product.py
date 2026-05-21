from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class ProductCategory(Base, TimestampMixin):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name_en = Column(String(200), nullable=False)
    name_cn = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True)

    products = relationship("Product", back_populates="category")
    children = relationship("ProductCategory", backref="parent", remote_side=[id])


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name_en = Column(String(300), nullable=False)
    name_cn = Column(String(300), nullable=False)
    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True)
    description = Column(Text, nullable=True)
    images = Column(JSON, default=list)
    specs = Column(JSON, default=dict)  # { "power": "450W", "voltage": "24V", ... }
    moq = Column(Integer, default=1)
    lead_time_days = Column(Integer, default=15)
    is_active = Column(Boolean, default=True)

    category = relationship("ProductCategory", back_populates="products")
    pricing_tiers = relationship("PricingTier", back_populates="product", order_by="PricingTier.quantity_min")


class PricingTier(Base, TimestampMixin):
    __tablename__ = "pricing_tiers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    tier_name = Column(String(100), nullable=False)  # 样品 / 小批 / 中批 / 大批
    quantity_min = Column(Integer, nullable=False)
    quantity_max = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    fob_price = Column(Float, nullable=True)
    cif_price = Column(Float, nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)

    product = relationship("Product", back_populates="pricing_tiers")
