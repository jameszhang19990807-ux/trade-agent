"""
Settings API — allows customer to self-configure WhatsApp and LLM
credentials without sharing them with the platform operator.
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.settings import TenantSetting

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Keys the customer is allowed to configure
EDITABLE_KEYS = {
    "whatsapp_phone_number_id",
    "whatsapp_token",
    "whatsapp_verify_token",
    "deepseek_api_key",
    "agent_name",
    "auto_reply_enabled",
}

KEY_LABELS = {
    "whatsapp_phone_number_id": "WhatsApp Phone Number ID",
    "whatsapp_token": "WhatsApp Token",
    "whatsapp_verify_token": "Webhook Verify Token",
    "deepseek_api_key": "DeepSeek API Key",
    "agent_name": "Agent Name",
    "auto_reply_enabled": "Auto Reply",
}


class SettingsUpdate(BaseModel):
    settings: dict[str, str]  # key → value


class PasswordMask(str):
    """Masks sensitive values for display."""
    @classmethod
    def mask(cls, value: str) -> str:
        if not value:
            return ""
        if len(value) <= 8:
            return "*" * len(value)
        return value[:4] + "*" * (len(value) - 8) + value[-4:]


@router.get("")
async def get_settings(request: Request):
    """Return all editable settings with masked values."""
    db: AsyncSession = request.state.db
    result = await db.execute(
        select(TenantSetting).where(TenantSetting.key.in_(EDITABLE_KEYS))
    )
    existing = {row.key: row.value for row in result.scalars().all()}

    items = []
    for key in sorted(EDITABLE_KEYS):
        value = existing.get(key, "")
        items.append({
            "key": key,
            "label": KEY_LABELS.get(key, key),
            "value": value,
            "masked": PasswordMask.mask(value),
            "is_set": bool(value),
        })

    return {"settings": items}


@router.put("")
async def update_settings(request: Request, body: SettingsUpdate):
    """Update settings. Only editable keys are accepted."""
    db: AsyncSession = request.state.db

    updated = []
    for key, value in body.settings.items():
        if key not in EDITABLE_KEYS:
            continue
        # Upsert
        result = await db.execute(
            select(TenantSetting).where(TenantSetting.key == key)
        )
        row = result.scalar_one_or_none()
        if row:
            row.value = value
        else:
            db.add(TenantSetting(key=key, value=value))
        updated.append(key)

    await db.commit()

    # Reload services with new credentials
    from ..services.whatsapp import reload_client
    from ..services.intent_engine import reload_engine
    reload_client()
    reload_engine()

    return {"status": "ok", "updated": updated}
