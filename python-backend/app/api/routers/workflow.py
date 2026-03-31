from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.database import db_session_dependency
from app.core.dependencies import get_current_user
from app.core.exceptions import BusinessException, ErrorCode
from app.core.response import success

router = APIRouter(prefix="/workflow", tags=["workflow"])


def _db(request: Request):
    yield from db_session_dependency(request.app.state.session_factory)


@router.post("/testing/promote-admin")
def promote_admin_for_testing(request: Request, _=Depends(get_current_user)):
    if not request.app.state.settings.testing:
        raise BusinessException(ErrorCode.FORBIDDEN_ERROR, "仅测试环境可用")
    db = next(_db(request))
    try:
        user = get_current_user(request)
        db_user = db.get(type(user), user.id)
        db_user.user_role = "admin"
        db.commit()
        return success(True)
    finally:
        db.close()
