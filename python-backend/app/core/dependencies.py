from __future__ import annotations

from fastapi import Request

from app.core.database import db_session_dependency
from app.core.exceptions import BusinessException, ErrorCode
from app.models.user import User


def get_settings(request: Request):
    return request.app.state.settings


def get_db(request: Request):
    yield from db_session_dependency(request.app.state.session_factory)


def get_ai_gateway(request: Request):
    return request.app.state.ai_gateway


def get_current_user(request: Request):
    session_generator = db_session_dependency(request.app.state.session_factory)
    db = next(session_generator)
    try:
        settings = request.app.state.settings
        session_store = request.app.state.session_store
        session_id = request.cookies.get(settings.session_cookie_name)
        if not session_id:
            raise BusinessException(ErrorCode.NOT_LOGIN_ERROR)
        user_id = session_store.get_user_id(session_id)
        if not user_id:
            raise BusinessException(ErrorCode.NOT_LOGIN_ERROR)
        user = db.get(User, user_id)
        if not user or user.is_delete:
            raise BusinessException(ErrorCode.NOT_LOGIN_ERROR)
        return user
    finally:
        try:
            next(session_generator)
        except StopIteration:
            pass


def require_admin(request: Request):
    user = get_current_user(request)
    if user.user_role != "admin":
        raise BusinessException(ErrorCode.NO_AUTH_ERROR)
    return user
