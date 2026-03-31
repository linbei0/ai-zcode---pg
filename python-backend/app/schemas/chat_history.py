from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ChatHistoryQueryRequest(BaseModel):
    pageNum: int = 1
    pageSize: int = 10
    sortField: str | None = None
    sortOrder: str | None = "descend"
    id: int | None = None
    message: str | None = None
    messageType: str | None = None
    appId: int | None = None
    userId: int | None = None
    lastCreateTime: datetime | None = None
