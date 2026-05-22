"""
Startup wrapper — catches and prints all import errors
so Render's logs actually show what went wrong.
"""
import sys
import traceback

print("=== Python startup ===", flush=True)
print(f"Python {sys.version}", flush=True)
print(f"sys.path: {sys.path}", flush=True)

# Test each import step by step
steps = [
    ("config", "from app.config import settings"),
    ("models.base", "from app.models.base import Base"),
    ("models.customer", "from app.models.customer import Customer"),
    ("models.product", "from app.models.product import Product, PricingTier, ProductCategory"),
    ("models.conversation", "from app.models.conversation import Conversation, Message"),
    ("services.whatsapp", "from app.services.whatsapp import whatsapp_client"),
    ("services.intent_engine", "from app.services.intent_engine import intent_engine"),
    ("services.price_library", "from app.services.price_library import price_library"),
    ("services.agent", "from app.services.agent import trade_agent"),
    ("routers.webhook", "from app.routers import webhook"),
    ("routers.dashboard", "from app.routers import dashboard"),
]

failed = False
for name, code in steps:
    try:
        exec(code)
        print(f"  [OK] {name}", flush=True)
    except Exception as e:
        print(f"  [FAIL] {name}: {e}", flush=True)
        traceback.print_exc()
        failed = True

if failed:
    print("=== IMPORT FAILURES DETECTED ===", flush=True)
    sys.exit(1)

print("=== All imports OK, creating app ===", flush=True)

# Import app for uvicorn
from app.main import app

print("=== App created, ready for uvicorn ===", flush=True)
