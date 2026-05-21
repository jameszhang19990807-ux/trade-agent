from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CustomerSummary(BaseModel):
    id: int
    whatsapp_number: str
    name: Optional[str]
    company_name: Optional[str]
    country: Optional[str]
    pipeline_stage: str
    total_inquiries: int
    total_orders: int
    last_contact_at: Optional[datetime]


class ConversationSummary(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    status: str
    is_human_handling: bool
    intent_code: Optional[str]
    auto_round_count: int
    last_message_preview: Optional[str]
    updated_at: datetime


class PipelineStats(BaseModel):
    stage: str
    count: int


class DashboardOverview(BaseModel):
    total_leads: int
    total_conversations: int
    auto_reply_rate: float
    conversion_rate: float
    pipeline: list[PipelineStats]
    recent_conversations: list[ConversationSummary]
