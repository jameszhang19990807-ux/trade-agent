from pydantic_settings import BaseSettings


def _build_db_url(raw: str) -> str:
    """Convert standard PostgreSQL URL to asyncpg format for SQLAlchemy."""
    if not raw or "sqlite" in raw:
        return raw or "sqlite+aiosqlite:///trade_agent.db"
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+asyncpg://", 1)
    return raw


class Settings(BaseSettings):
    # Database
    # Render sets DATABASE_URL as env var; local dev defaults to SQLite
    database_url: str = "sqlite+aiosqlite:///trade_agent.db"

    @property
    def async_database_url(self) -> str:
        return _build_db_url(self.database_url)

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "+psycopg2").replace("+aiosqlite", "")

    redis_url: str = ""

    # LLM
    llm_provider: str = "deepseek"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_model: str = "deepseek-chat"

    # WhatsApp
    whatsapp_phone_number_id: str = ""
    whatsapp_token: str = ""
    whatsapp_verify_token: str = "trade_agent_verify_2024"
    whatsapp_api_version: str = "v19.0"

    # Agent
    agent_name: str = "TradeBot"
    auto_reply_enabled: bool = True
    human_takeover_threshold: float = 0.7
    max_auto_rounds: int = 3
    large_order_threshold_usd: float = 10000.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
