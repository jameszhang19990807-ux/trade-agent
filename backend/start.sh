#!/bin/bash
set -e

echo "=== Trade Agent Startup ==="
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "PORT: $PORT"
echo "PYTHON_VERSION: ${PYTHON_VERSION:-not set}"
echo "DATABASE_URL: ${DATABASE_URL:+set (${#DATABASE_URL} chars)}"
echo "DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY:+set (${#DEEPSEEK_API_KEY} chars)}"

echo ""
echo "=== Testing imports ==="
python -c "from app.config import settings; print(f'DB URL: {settings.async_database_url[:50]}...')" || echo "CONFIG FAILED"
python -c "from app.models.base import Base; print('models.base OK')" || echo "MODELS.BASE FAILED"
python -c "from app.models.customer import Customer; print('models.customer OK')" || echo "MODELS.CUSTOMER FAILED"
python -c "from app.models.product import Product; print('models.product OK')" || echo "MODELS.PRODUCT FAILED"
python -c "from app.models.conversation import Conversation; print('models.conversation OK')" || echo "MODELS.CONVERSATION FAILED"
python -c "from app.services.whatsapp import whatsapp_client; print('services.whatsapp OK')" || echo "SERVICES.WHATSAPP FAILED"
python -c "from app.services.intent_engine import intent_engine; print('services.intent_engine OK')" || echo "SERVICES.INTENT_ENGINE FAILED"
python -c "from app.services.price_library import price_library; print('services.price_library OK')" || echo "SERVICES.PRICE_LIBRARY FAILED"
python -c "from app.services.agent import trade_agent; print('services.agent OK')" || echo "SERVICES.AGENT FAILED"

echo ""
echo "=== Starting uvicorn ==="
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --log-level info
