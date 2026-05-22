"""
WhatsApp Cloud API webhook endpoint.
Receives incoming messages and delegates to the TradeAgent.
"""
import json
import logging

from fastapi import APIRouter, Request, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.agent import trade_agent
from ..services.whatsapp import whatsapp_client
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
):
    """Meta webhook verification endpoint."""
    ok, response = whatsapp_client.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    if ok:
        try:
            return int(hub_challenge)
        except (ValueError, TypeError):
            return hub_challenge or "OK"
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def receive_whatsapp(request: Request):
    """Receive incoming WhatsApp messages."""
    db: AsyncSession = request.state.db

    body = await request.json()
    logger.info(f"Webhook received: {json.dumps(body, indent=2)}")

    try:
        entries = body.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for msg in messages:
                    msg_type = msg.get("type", "text")
                    msg_id = msg.get("id", "")

                    # Mark as read (non-fatal)
                    try:
                        await whatsapp_client.mark_as_read(msg_id)
                    except Exception:
                        pass

                    if msg_type == "text":
                        text = msg.get("text", {}).get("body", "")
                        from_number = msg.get("from", "")

                        if text and from_number:
                            result = await trade_agent.process_incoming_message(
                                db=db,
                                whatsapp_number=from_number,
                                message_text=text,
                                message_id=msg_id,
                            )
                            logger.info(f"Agent result: {result}")

        return {"status": "ok"}

    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}
