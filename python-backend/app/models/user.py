from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    user_account: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    user_password: Mapped[str] = mapped_column(String(512), nullable=False)
    user_name: Mapped[str | None] = mapped_column(String(256))
    user_avatar: Mapped[str | None] = mapped_column(String(1024))
    user_profile: Mapped[str | None] = mapped_column(String(512))
    user_role: Mapped[str] = mapped_column(String(256), default="user", nullable=False)
    edit_time: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
