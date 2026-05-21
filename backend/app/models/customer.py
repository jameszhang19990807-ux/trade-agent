from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    whatsapp_number = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=True)
    company_name = Column(String(300), nullable=True)
    country = Column(String(100), nullable=True)
    language = Column(String(20), default="en")
    email = Column(String(200), nullable=True)

    # Pipeline stage
    pipeline_stage = Column(String(50), default="new_lead", index=True)
    # new_lead / replied / deep_talk / sample_trial / formal_order / won / lost / dormant

    # Stats
    total_inquiries = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    total_value_usd = Column(Float, default=0.0)
    last_contact_at = Column(DateTime(timezone=True), nullable=True)

    # Preferences
    preferred_products = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    notes = Column(Text, nullable=True)

    conversations = relationship("Conversation", back_populates="customer")

    @property
    def display_name(self):
        return self.name or self.company_name or self.whatsapp_number
