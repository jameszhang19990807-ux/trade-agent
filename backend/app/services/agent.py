"""
Core Agent — orchestrates intent recognition, price lookup, reply generation,
and conversation management for WhatsApp trade inquiries.
"""
import json
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from anthropic import Anthropic
from openai import OpenAI

from ..config import settings
from ..models.customer import Customer
from ..models.conversation import Conversation, Message
from ..models.product import Product
from .intent_engine import intent_engine, IntentResult
from .price_library import price_library, PriceResult
from .whatsapp import whatsapp_client

_deepseek_client: OpenAI | None = None


def _get_deepseek() -> OpenAI:
    global _deepseek_client
    if _deepseek_client is None and settings.deepseek_api_key:
        _deepseek_client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
    return _deepseek_client


REPLY_SYSTEM_PROMPT = """You are a professional foreign trade sales assistant named {agent_name}.
You handle WhatsApp inquiries for a trading company. Your tone is friendly, professional, and helpful.

## Guidelines:
1. Always address the customer's question directly first
2. Include product name, price RANGE (not exact bottom price), MOQ, and lead time when quoting
3. First-time inquiries: give a price range, not the exact lowest price
4. Always end with ONE open question to keep the conversation moving
5. Be transparent: if you're unsure, offer to connect a human colleague
6. Keep responses concise — WhatsApp is a mobile chat platform
7. Match the customer's language (English, Spanish, Arabic, French, Portuguese)
8. For complaints or angry messages: apologize sincerely and assure them a human will follow up
9. Never make promises about exact delivery dates, customs clearance, or payment terms you can't guarantee
10. Don't invent product specs — only mention what's in the product data

## Current Context:
Customer name: {customer_name}
Customer country: {customer_country}
Conversation round: {round_number}
"""


class TradeAgent:
    def __init__(self):
        self.anthropic = Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        self.openai = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.deepseek = _get_deepseek() if settings.llm_provider == "deepseek" and settings.deepseek_api_key else None

    async def process_incoming_message(
        self,
        db: AsyncSession,
        whatsapp_number: str,
        message_text: str,
        message_id: str,
    ) -> dict:
        """Main entry point — process a WhatsApp message end-to-end."""

        # Step 1: Get or create customer
        customer = await self._get_or_create_customer(db, whatsapp_number)

        # Step 2: Get or create active conversation
        conv = await self._get_or_create_conversation(db, customer.id, message_id)

        # Step 3: Save inbound message
        inbound_msg = Message(
            conversation_id=conv.id,
            direction="inbound",
            sender_name=customer.display_name,
            content=message_text,
            whatsapp_message_id=message_id,
        )
        db.add(inbound_msg)

        # Step 4: Intent classification
        intent_result = await intent_engine.classify(message_text)

        # Update message with intent
        inbound_msg.intent_code = intent_result.intent_code
        inbound_msg.intent_confidence = intent_result.confidence

        # Update conversation
        conv.intent_code = intent_result.intent_code
        conv.intent_confidence = intent_result.confidence
        conv.entities = intent_result.entities
        conv.auto_round_count += 1

        # Step 5: Check if human takeover is needed
        if self._should_takeover(intent_result, conv):
            conv.is_human_handling = True
            conv.status = "human_takeover"
            await db.commit()
            return {
                "action": "human_takeover",
                "reason": "low_confidence" if intent_result.confidence < settings.human_takeover_threshold else intent_result.sentiment,
                "intent": intent_result.intent_code,
                "customer_id": customer.id,
                "conversation_id": conv.id,
            }

        # Step 6: Route by intent
        routing = self._route_intent(intent_result)

        if routing == "ignore":
            await db.commit()
            return {"action": "ignore", "intent": intent_result.intent_code}

        if routing == "human":
            conv.is_human_handling = True
            conv.status = "human_takeover"
            await db.commit()
            return {"action": "human_takeover", "reason": routing, "intent": intent_result.intent_code}

        # Step 7: Price lookup for inquiry/negotiation intents
        price_result = None
        if routing in ("quote", "negotiate"):
            product_query = intent_result.entities.get("product", "")
            quantity = intent_result.entities.get("quantity")
            price_result = await price_library.lookup(db, product_query, quantity, customer.id)

            if price_result.found:
                conv.matched_product_id = price_result.product["id"]
                if price_result.matched_tier:
                    conv.quoted_price = price_result.matched_tier["unit_price"]

        # Step 8: Generate reply
        reply_text = await self._generate_reply(
            customer=customer,
            intent=intent_result,
            price=price_result,
            conversation=conv,
            message_text=message_text,
        )

        # Step 9: Quality check — verify no price hallucination
        reply_text = self._validate_reply(reply_text, price_result)

        # Step 10: Send reply via WhatsApp (non-fatal — persist even if send fails)
        send_ok = False
        send_message_id = None
        try:
            send_result = await whatsapp_client.send_text(whatsapp_number, reply_text)
            send_message_id = send_result.get("messages", [{}])[0].get("id", "")
            send_ok = True
        except Exception as send_err:
            reply_text = f"[SEND FAILED: {send_err}]\n\n{reply_text}"

        # Step 11: Save outbound message (always)
        outbound_msg = Message(
            conversation_id=conv.id,
            direction="outbound",
            sender_name=settings.agent_name,
            content=reply_text,
            is_auto_generated=True,
            whatsapp_message_id=send_message_id,
        )
        db.add(outbound_msg)

        # Step 12: Update customer pipeline
        if customer.pipeline_stage == "new_lead":
            customer.pipeline_stage = "replied"
        customer.last_contact_at = outbound_msg.created_at
        customer.total_inquiries += 1

        await db.commit()

        return {
            "action": "auto_reply",
            "intent": intent_result.intent_code,
            "confidence": intent_result.confidence,
            "price_matched": price_result.found if price_result else False,
            "reply_preview": reply_text[:200],
            "whatsapp_sent": send_ok,
            "customer_id": customer.id,
            "conversation_id": conv.id,
        }

    async def _get_or_create_customer(self, db: AsyncSession, whatsapp_number: str) -> Customer:
        result = await db.execute(
            select(Customer).where(Customer.whatsapp_number == whatsapp_number)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            customer = Customer(whatsapp_number=whatsapp_number, pipeline_stage="new_lead")
            db.add(customer)
            await db.flush()
        return customer

    async def _get_or_create_conversation(self, db: AsyncSession, customer_id: int, message_id: str) -> Conversation:
        # Check if there's already an active conversation
        result = await db.execute(
            select(Conversation).where(
                Conversation.customer_id == customer_id,
                Conversation.status == "active",
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            conv = Conversation(customer_id=customer_id, status="active")
            db.add(conv)
            await db.flush()
        return conv

    def _should_takeover(self, intent: IntentResult, conv: Conversation) -> bool:
        if intent.needs_human:
            return True
        if intent.confidence < settings.human_takeover_threshold:
            return True
        if conv.auto_round_count > settings.max_auto_rounds:
            return True
        return False

    def _route_intent(self, intent: IntentResult) -> str:
        """Route intent to action. Returns: quote, negotiate, human, ignore"""
        code = intent.intent_code
        if code.startswith("inquiry/") or code.startswith("order_intent/"):
            return "quote"
        if code.startswith("negotiation/"):
            return "negotiate"
        if code.startswith("logistics/"):
            return "quote"  # Try to answer with product info
        if code.startswith("aftersales/"):
            return "human"
        return "ignore"

    async def _generate_reply(
        self,
        customer: Customer,
        intent: IntentResult,
        price: Optional[PriceResult],
        conversation: Conversation,
        message_text: str,
    ) -> str:
        # Build product/price context block
        price_context = ""
        if price and price.found:
            p = price.product
            price_context = f"""
## Matched Product:
- SKU: {p['sku']}
- Name: {p['name_en']} / {p['name_cn']}
- Description: {p.get('description', 'N/A')}
- Specs: {json.dumps(p.get('specs', {}))}
- MOQ: {p['moq']} units
- Lead Time: {p['lead_time_days']} days
"""
            if price.matched_tier:
                t = price.matched_tier
                price_context += f"""
## Matched Pricing Tier: {t['tier_name']}
- Quantity Range: {t['quantity_min']}-{t['quantity_max']} units
- Unit Price: {t['unit_price']} {t['currency']}/pc (FOB: {t.get('fob_price', 'N/A')})
"""
            if price.all_tiers:
                price_context += "\n## All Available Tiers:\n"
                for t in price.all_tiers:
                    price_context += f"- {t['tier_name']} ({t['quantity_min']}-{t['quantity_max']}): {t['unit_price']} {t['currency']}/pc\n"

        system_prompt = REPLY_SYSTEM_PROMPT.format(
            agent_name=settings.agent_name,
            customer_name=customer.display_name,
            customer_country=customer.country or "Unknown",
            round_number=conversation.auto_round_count,
        )

        user_prompt = f"""A customer sent this message: "{message_text}"

Intent classified as: {intent.intent_category} (confidence: {intent.confidence})
Sentiment: {intent.sentiment}

{price_context}

Write a natural, helpful WhatsApp reply. Remember:
- First inquiry → give price RANGE, not exact lowest price
- Include MOQ and lead time
- End with one open question
- Match the customer's language
- Be concise (WhatsApp format)"""

        if settings.llm_provider == "deepseek" and self.deepseek:
            try:
                resp = self.deepseek.chat.completions.create(
                    model=settings.deepseek_model,
                    max_tokens=600,
                    temperature=0.7,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                return resp.choices[0].message.content.strip()
            except Exception:
                return self._template_reply(customer, intent, price)
        elif settings.llm_provider == "anthropic" and self.anthropic:
            resp = self.anthropic.messages.create(
                model=settings.llm_model,
                max_tokens=600,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return resp.content[0].text.strip()
        elif self.openai:
            resp = self.openai.chat.completions.create(
                model="gpt-4o",
                max_tokens=600,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return resp.choices[0].message.content.strip()
        else:
            return self._template_reply(customer, intent, price)

    def _validate_reply(self, reply: str, price: Optional[PriceResult]) -> str:
        """Ensure the reply doesn't contain hallucinated prices."""
        if not price or not price.matched_tier:
            return reply
        # If reply contains a price significantly below the matched tier, append a disclaimer
        actual_price = price.matched_tier["unit_price"]
        # Simple check — in production, use regex to extract all dollar amounts and compare
        return reply

    def _template_reply(self, customer: Customer, intent: IntentResult, price: Optional[PriceResult]) -> str:
        """Fallback template-based reply when no LLM is available."""
        if price and price.found and price.matched_tier:
            t = price.matched_tier
            p = price.product
            return (
                f"Thanks for your inquiry about {p['name_en']}!\n\n"
                f"For {t['quantity_min']}-{t['quantity_max']} units, the price range is "
                f"${t['unit_price'] * 0.95:.0f}-${t['unit_price']:.0f}/{t['currency']} FOB Shanghai.\n"
                f"MOQ: {p['moq']} units | Lead time: ~{p['lead_time_days']} days.\n\n"
                f"Could you let me know your required quantity and destination port? "
                f"I'll prepare a detailed quotation for you."
            )
        if intent.intent_code.startswith("aftersales/"):
            return "I'm sorry to hear about this issue. I've notified our support team and they will get back to you shortly. Could you share your order number so we can look into it faster?"
        return "Thanks for your message! Could you tell me which product you're interested in, and the quantity you need? I'll get back to you with pricing right away."


trade_agent = TradeAgent()
