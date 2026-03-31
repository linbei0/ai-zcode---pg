from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException, ErrorCode
from app.models.app import App
from app.models.chat_history import ChatHistory
from app.models.user import User
from app.repositories.chat_history_repository import ChatHistoryRepository
from app.schemas.chat_history import ChatHistoryQueryRequest


class ChatHistoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ChatHistoryRepository(db)

    def add_chat_message(self, app_id: int, message: str, message_type: str, user_id: int) -> bool:
        item = ChatHistory(
            message=message,
            message_type=message_type,
            app_id=app_id,
            user_id=user_id,
        )
        self.repository.save(item)
        self.db.commit()
        return True

    def list_app_chat_history_by_page(
        self,
        app_id: int,
        page_size: int,
        last_create_time: datetime | None,
        login_user: User,
    ) -> tuple[list[dict], int]:
        if app_id <= 0:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "应用ID不能为空")
        if page_size <= 0 or page_size > 50:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "页面大小必须在1-50之间")
        app = self.db.get(App, app_id)
        if not app or app.is_delete:
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "应用不存在")
        if login_user.user_role != "admin" and app.user_id != login_user.id:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "无权查看该应用的对话历史")

        stmt = select(ChatHistory).where(ChatHistory.app_id == app_id, ChatHistory.is_delete == 0)
        count_stmt = select(func.count(ChatHistory.id)).where(ChatHistory.app_id == app_id, ChatHistory.is_delete == 0)
        if last_create_time:
            stmt = stmt.where(ChatHistory.create_time < last_create_time)
            count_stmt = count_stmt.where(ChatHistory.create_time < last_create_time)
        stmt = stmt.order_by(ChatHistory.create_time.desc()).limit(page_size)
        records = self.db.execute(stmt).scalars().all()
        total = self.db.execute(count_stmt).scalar_one()
        return [self.to_dict(item) for item in records], total

    def list_admin_page(self, query: ChatHistoryQueryRequest) -> tuple[list[dict], int]:
        stmt = select(ChatHistory).where(ChatHistory.is_delete == 0)
        count_stmt = select(func.count(ChatHistory.id)).where(ChatHistory.is_delete == 0)
        if query.id:
            stmt = stmt.where(ChatHistory.id == query.id)
            count_stmt = count_stmt.where(ChatHistory.id == query.id)
        if query.message:
            stmt = stmt.where(ChatHistory.message.like(f"%{query.message}%"))
            count_stmt = count_stmt.where(ChatHistory.message.like(f"%{query.message}%"))
        if query.messageType:
            stmt = stmt.where(ChatHistory.message_type == query.messageType)
            count_stmt = count_stmt.where(ChatHistory.message_type == query.messageType)
        if query.appId:
            stmt = stmt.where(ChatHistory.app_id == query.appId)
            count_stmt = count_stmt.where(ChatHistory.app_id == query.appId)
        if query.userId:
            stmt = stmt.where(ChatHistory.user_id == query.userId)
            count_stmt = count_stmt.where(ChatHistory.user_id == query.userId)
        if query.lastCreateTime:
            stmt = stmt.where(ChatHistory.create_time < query.lastCreateTime)
            count_stmt = count_stmt.where(ChatHistory.create_time < query.lastCreateTime)

        stmt = self._apply_sort(stmt, query.sortField, query.sortOrder)
        total = self.db.execute(count_stmt).scalar_one()
        offset = (query.pageNum - 1) * query.pageSize
        records = self.db.execute(stmt.offset(offset).limit(query.pageSize)).scalars().all()
        return [self.to_dict(item) for item in records], total

    def build_history_text(self, app_id: int) -> str:
        stmt = (
            select(ChatHistory)
            .where(ChatHistory.app_id == app_id, ChatHistory.is_delete == 0)
            .order_by(ChatHistory.create_time.asc())
        )
        records = self.db.execute(stmt).scalars().all()
        lines = [f"{item.message_type}: {item.message}" for item in records]
        return "\n".join(lines)

    def to_dict(self, item: ChatHistory) -> dict:
        return {
            "id": item.id,
            "message": item.message,
            "messageType": item.message_type,
            "appId": item.app_id,
            "userId": item.user_id,
            "createTime": item.create_time.isoformat() if item.create_time else None,
            "updateTime": item.update_time.isoformat() if item.update_time else None,
            "isDelete": item.is_delete,
        }

    def _apply_sort(self, stmt, sort_field: str | None, sort_order: str | None):
        mapping = {
            "id": ChatHistory.id,
            "create_time": ChatHistory.create_time,
            "update_time": ChatHistory.update_time,
        }
        column = mapping.get(sort_field or "", ChatHistory.create_time)
        if sort_order in {"asc", "ascend"}:
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())
