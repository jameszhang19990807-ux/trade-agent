"""
WhatsApp Cloud API client.
"""
import httpx
from ..config import settings


class WhatsAppClient:
    def __init__(self):
        self.base_url = f"https://graph.facebook.com/{settings.whatsapp_api_version}/{settings.whatsapp_phone_number_id}"
        self.token = settings.whatsapp_token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def send_text(self, to_number: str, text: str) -> dict:
        url = f"{self.base_url}/messages"
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
        """Send a pre-approved template message — required for out-of-24h-window replies."""
        url = f"{self.base_url}/messages"
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
        url = f"{self.base_url}/messages"
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
        url = f"{self.base_url}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload, headers=self._headers())
            return resp.json()

    def verify_webhook(self, mode: str, token: str, challenge: str) -> tuple[bool, str]:
        if mode == "subscribe" and token == settings.whatsapp_verify_token:
            return True, challenge
        return False, "Verification failed"


whatsapp_client = WhatsAppClient()
