from sqlalchemy import Column, String, Text
from .base import Base


class TenantSetting(Base):
    __tablename__ = "tenant_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, default="")
