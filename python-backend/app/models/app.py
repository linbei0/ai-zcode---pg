from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class App(Base, TimestampMixin):
    __tablename__ = "app"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    app_name: Mapped[str | None] = mapped_column(String(256))
    cover: Mapped[str | None] = mapped_column(String(512))
    init_prompt: Mapped[str | None] = mapped_column(Text)
    code_gen_type: Mapped[str | None] = mapped_column(String(64))
    deploy_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    deployed_time: Mapped[datetime | None] = mapped_column(DateTime)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    edit_time: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
