from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    ForeignKey, Text, JSON, Boolean
)
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    whatsapp_message_id = Column(String(100), unique=True, nullable=True)
    status = Column(String(30), default="active")  # active / human_takeover / closed
    is_human_handling = Column(Boolean, default=False)
    intent_code = Column(String(50), nullable=True)
    intent_confidence = Column(Float, nullable=True)
    entities = Column(JSON, nullable=True)
    matched_product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    quoted_price = Column(Float, nullable=True)
    auto_round_count = Column(Integer, default=0)

    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # "inbound" or "outbound"
    sender_name = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default="text")  # text / image / document / location
    media_url = Column(String(500), nullable=True)
    intent_code = Column(String(50), nullable=True)
    intent_confidence = Column(Float, nullable=True)
    is_auto_generated = Column(Boolean, default=False)
    whatsapp_message_id = Column(String(100), nullable=True, unique=True)

    conversation = relationship("Conversation", back_populates="messages")
