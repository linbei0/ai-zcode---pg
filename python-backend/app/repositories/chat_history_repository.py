from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory


class ChatHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, item: ChatHistory) -> ChatHistory:
        self.db.add(item)
        self.db.flush()
        return item
