from pydantic import BaseModel
from typing import Optional


class WhatsAppWebhookEntry(BaseModel):
    id: str
    changes: list


class WhatsAppMessage(BaseModel):
    from_number: str
    message_id: str
    text: str
    timestamp: str


class WebhookResponse(BaseModel):
    status: str
    action: Optional[str] = None
    message: Optional[str] = None
