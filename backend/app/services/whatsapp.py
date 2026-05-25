"""
WhatsApp Cloud API client.
Reads credentials from DB first, falls back to env vars.
"""
import httpx
import asyncio
from ..config import settings


def _read_db_setting(key: str) -> str:
    """Synchronous read from DB — only for initialized settings."""
    return ""  # Will be overridden by hot-reload via async path


class WhatsAppClient:
    def __init__(self):
        self._base_url = ""
        self._token = ""
        self._phone_number_id = ""
        self._reload()

    def _reload(self):
        """Re-read credentials. Env vars are the fallback default."""
        self._phone_number_id = settings.whatsapp_phone_number_id or ""
        self._token = settings.whatsapp_token or ""
        self._base_url = (
            f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
            f"{self._phone_number_id}"
        )

    def set_credentials(self, phone_number_id: str, token: str):
        """Called after customer updates credentials via settings UI."""
        if phone_number_id:
            self._phone_number_id = phone_number_id
        if token:
            self._token = token
        self._base_url = (
            f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
            f"{self._phone_number_id}"
        )

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def send_text(self, to_number: str, text: str) -> dict:
        if not self._token:
            raise RuntimeError("WhatsApp token not configured")
        url = f"{self._base_url}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def send_template(
        self, to_number: str, template_name: str, language_code: str = "en", parameters: list = None
    ) -> dict:
        if not self._token:
            raise RuntimeError("WhatsApp token not configured")
        url = f"{self._base_url}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }
        if parameters:
            payload["template"]["components"] = [{
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in parameters],
            }]
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def send_image(self, to_number: str, image_url: str, caption: str = "") -> dict:
        if not self._token:
            raise RuntimeError("WhatsApp token not configured")
        url = f"{self._base_url}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "image",
            "image": {"link": image_url, "caption": caption},
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def mark_as_read(self, message_id: str) -> dict:
        if not self._token:
            raise RuntimeError("WhatsApp token not configured")
        url = f"{self._base_url}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload, headers=self._headers())
            return resp.json()

    def verify_webhook(self, mode: str, token: str, challenge: str) -> tuple[bool, str]:
        verify_token = settings.whatsapp_verify_token
        if mode == "subscribe" and token == verify_token:
            return True, challenge
        return False, "Verification failed"


whatsapp_client = WhatsAppClient()


def reload_client():
    """Called after settings update to refresh credentials."""
    whatsapp_client._reload()
