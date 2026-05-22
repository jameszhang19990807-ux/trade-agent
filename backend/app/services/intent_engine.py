"""
Intent Engine — LLM-based intent classification for foreign trade inquiries.
Supports English, Spanish, Arabic, French, Portuguese.
"""
import json
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI

from ..config import settings

# DeepSeek uses OpenAI-compatible API with a different base URL
_deepseek_client: OpenAI | None = None


def _get_deepseek() -> OpenAI:
    global _deepseek_client
    if _deepseek_client is None and settings.deepseek_api_key:
        _deepseek_client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
    return _deepseek_client


@dataclass
class IntentResult:
    intent_code: str           # e.g. "inquiry/specific_model"
    intent_category: str       # e.g. "产品询价"
    confidence: float
    entities: dict = field(default_factory=dict)
    language: str = "en"
    sentiment: str = "neutral"  # positive / neutral / negative
    needs_human: bool = False
    raw_response: str = ""


INTENT_DEFINITIONS = """
## Intent Taxonomy for Foreign Trade

### inquiry/specific_model
Customer asks about a specific product model or SKU.
Examples: "What's the price of Model X500?", "I need quotation for SP-450"

### inquiry/general_category
Customer asks about a product category without a specific model.
Examples: "I need LED panels", "Do you have solar inverters?"

### order_intent/sample
Customer wants a sample before bulk order.
Examples: "Can you send me a sample?", "I want to test one unit first"

### order_intent/bulk
Customer indicates a specific quantity for purchase.
Examples: "I want 500 units", "We need 1000pcs for our project"

### logistics/shipping
Questions about shipping cost, time, or method.
Examples: "How much to ship to Dubai?", "What's the delivery time to Lagos?"

### logistics/customs
Questions about customs, duties, packaging for export.
Examples: "What about customs clearance?", "How do you pack for sea freight?"

### aftersales/complaint
Customer complains about quality, delivery, or service.
Examples: "The last batch had defects", "You sent wrong items"

### aftersales/installation
Questions about installation, usage, or maintenance.
Examples: "How to install?", "What's the warranty?"

### negotiation/price
Customer negotiates for a better price.
Examples: "Can you give discount?", "Your competitor offers $50"

### negotiation/payment
Questions about payment terms.
Examples: "Do you accept LC?", "Can I pay 30% deposit?"

### other
Not a business inquiry — spam, greetings, irrelevant messages.
Examples: "Hi", "Thank you", promotional messages
"""

SYSTEM_PROMPT = f"""You are an intent classifier for a foreign trade automation system.
Analyze the customer message and output a JSON object with the following fields:

- intent_code: one of the codes from the taxonomy
- confidence: float 0.0-1.0 (how confident you are)
- entities: extract these entities if present:
  - product: product name or model mentioned
  - quantity: number of units mentioned (integer)
  - destination: country or port mentioned for shipping
  - payment_method: LC, TT, etc.
  - competitor_price: any competitor price mentioned
- language: ISO 639-1 code of the message language
- sentiment: "positive" / "neutral" / "negative"
- needs_human: true if the message is angry, urgent, or explicitly requests human contact

{INTENT_DEFINITIONS}

Output ONLY valid JSON, no other text."""


class IntentEngine:
    def __init__(self):
        self.openai = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def classify(self, message_text: str) -> IntentResult:
        if settings.llm_provider == "deepseek" and settings.deepseek_api_key:
            return await self._classify_openai_compat(message_text)
        elif self.openai:
            return await self._classify_openai(message_text)
        else:
            return self._fallback_classify(message_text)

    async def _classify_openai_compat(self, message_text: str) -> IntentResult:
        """DeepSeek or any OpenAI-compatible provider. Falls back to keyword on failure."""
        client = _get_deepseek()
        if not client:
            return self._fallback_classify(message_text)
        try:
            resp = client.chat.completions.create(
                model=settings.deepseek_model,
                max_tokens=512,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message_text},
                ],
            )
            return self._parse_response(resp.choices[0].message.content)
        except Exception:
            return self._fallback_classify(message_text)

    async def _classify_openai(self, message_text: str) -> IntentResult:
        resp = self.openai.chat.completions.create(
            model="gpt-4o",
            max_tokens=512,
            temperature=0.0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message_text},
            ],
        )
        return self._parse_response(resp.choices[0].message.content)

    def _parse_response(self, raw: str) -> IntentResult:
        try:
            # Strip markdown code fences if present
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                if raw.endswith("```"):
                    raw = raw[:-3]
            data = json.loads(raw)
        except json.JSONDecodeError:
            return IntentResult(
                intent_code="other",
                intent_category="其他",
                confidence=0.3,
                needs_human=True,
                raw_response=raw,
            )

        intent_map = {
            "inquiry/specific_model": "产品询价-型号",
            "inquiry/general_category": "产品询价-品类",
            "order_intent/sample": "订单意向-样品",
            "order_intent/bulk": "订单意向-批量",
            "logistics/shipping": "物流咨询-运费",
            "logistics/customs": "物流咨询-关税",
            "aftersales/complaint": "售后-投诉",
            "aftersales/installation": "售后-安装",
            "negotiation/price": "商务谈判-价格",
            "negotiation/payment": "商务谈判-付款",
            "other": "其他",
        }

        intent_code = data.get("intent_code", "other")
        confidence = float(data.get("confidence", 0.5))

        return IntentResult(
            intent_code=intent_code,
            intent_category=intent_map.get(intent_code, "其他"),
            confidence=confidence,
            entities=data.get("entities", {}),
            language=data.get("language", "en"),
            sentiment=data.get("sentiment", "neutral"),
            needs_human=data.get("needs_human", False) or confidence < settings.human_takeover_threshold,
            raw_response=raw,
        )

    def _fallback_classify(self, message_text: str) -> IntentResult:
        """Keyword-based fallback when no LLM is available."""
        text_lower = message_text.lower()

        if any(w in text_lower for w in ["price", "quotation", "quote", "how much", "cost"]):
            return IntentResult(intent_code="inquiry/general_category", intent_category="产品询价-品类", confidence=0.5, entities={})
        if any(w in text_lower for w in ["sample", "test unit", "trial"]):
            return IntentResult(intent_code="order_intent/sample", intent_category="订单意向-样品", confidence=0.5, entities={})
        if any(w in text_lower for w in ["shipping", "delivery", "freight", "ship to"]):
            return IntentResult(intent_code="logistics/shipping", intent_category="物流咨询-运费", confidence=0.5, entities={})
        if any(w in text_lower for w in ["discount", "cheaper", "lower price", "best price"]):
            return IntentResult(intent_code="negotiation/price", intent_category="商务谈判-价格", confidence=0.5, entities={})
        if any(w in text_lower for w in ["complaint", "defect", "wrong", "bad quality"]):
            return IntentResult(intent_code="aftersales/complaint", intent_category="售后-投诉", confidence=0.5, entities={}, sentiment="negative", needs_human=True)
        return IntentResult(intent_code="other", intent_category="其他", confidence=0.3, entities={})


intent_engine = IntentEngine()
