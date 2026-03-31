from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Request

from app.core.database import db_session_dependency
from app.core.dependencies import get_current_user, require_admin
from app.core.response import build_page, success
from app.schemas.chat_history import ChatHistoryQueryRequest
from app.services.chat_history_service import ChatHistoryService

router = APIRouter(prefix="/chatHistory", tags=["chatHistory"])


def _db(request: Request):
    yield from db_session_dependency(request.app.state.session_factory)


@router.get("/app/{app_id}")
def list_app_chat_history(
    app_id: int,
    request: Request,
    pageSize: int = 10,
    lastCreateTime: datetime | None = None,
    _=Depends(get_current_user),
):
    db = next(_db(request))
    try:
        login_user = get_current_user(request)
        records, total = ChatHistoryService(db).list_app_chat_history_by_page(
            app_id, pageSize, lastCreateTime, login_user
        )
        return success(build_page(records, 1, pageSize, total))
    finally:
        db.close()


@router.post("/admin/list/page/vo")
def list_all_chat_history_for_admin(
    payload: ChatHistoryQueryRequest,
    request: Request,
    _=Depends(require_admin),
):
    db = next(_db(request))
    try:
        records, total = ChatHistoryService(db).list_admin_page(payload)
        return success(build_page(records, payload.pageNum, payload.pageSize, total))
    finally:
        db.close()
