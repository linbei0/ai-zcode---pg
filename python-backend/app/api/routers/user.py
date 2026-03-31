from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response

from app.core.database import db_session_dependency
from app.core.dependencies import get_current_user, require_admin
from app.core.exceptions import BusinessException, ErrorCode
from app.core.response import build_page, success
from app.core.sessions import generate_session_id
from app.schemas.common import DeleteRequest
from app.schemas.user import (
    UserAddRequest,
    UserLoginRequest,
    UserQueryRequest,
    UserRegisterRequest,
    UserUpdateRequest,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/user", tags=["user"])


def _db(request: Request):
    yield from db_session_dependency(request.app.state.session_factory)


@router.post("/register")
def user_register(payload: UserRegisterRequest, request: Request):
    db = next(_db(request))
    try:
        user_id = UserService(db).register(payload.userAccount, payload.userPassword, payload.checkPassword)
        return success(user_id)
    finally:
        db.close()


@router.post("/login")
def user_login(payload: UserLoginRequest, response: Response, request: Request):
    db = next(_db(request))
    try:
        settings = request.app.state.settings
        session_store = request.app.state.session_store
        user = UserService(db).login(payload.userAccount, payload.userPassword)
        session_id = generate_session_id()
        session_store.set_user_id(session_id, user.id, settings.session_ttl_seconds)
        response.set_cookie(
            settings.session_cookie_name,
            session_id,
            httponly=True,
            samesite="lax",
            max_age=settings.session_ttl_seconds,
            path="/",
        )
        return success(UserService(db).to_login_user_vo(user))
    finally:
        db.close()


@router.get("/get/login")
def get_login_user(request: Request, _=Depends(get_current_user)):
    db = next(_db(request))
    try:
        user = get_current_user(request)
        return success(UserService(db).to_login_user_vo(user))
    finally:
        db.close()


@router.post("/logout")
def user_logout(response: Response, request: Request, _=Depends(get_current_user)):
    settings = request.app.state.settings
    session_store = request.app.state.session_store
    session_id = request.cookies.get(settings.session_cookie_name)
    if not session_id:
        raise BusinessException(ErrorCode.OPERATION_ERROR, "未登录")
    session_store.delete(session_id)
    response.delete_cookie(settings.session_cookie_name, path="/")
    return success(True)


@router.post("/add")
def add_user(payload: UserAddRequest, request: Request, _=Depends(require_admin)):
    db = next(_db(request))
    try:
        return success(UserService(db).add_user(payload))
    finally:
        db.close()


@router.get("/get")
def get_user(id: int, request: Request, _=Depends(require_admin)):
    db = next(_db(request))
    try:
        user = UserService(db).get_user(id)
        return success(
            {
                "id": user.id,
                "userAccount": user.user_account,
                "userPassword": user.user_password,
                "userName": user.user_name,
                "userAvatar": user.user_avatar,
                "userProfile": user.user_profile,
                "userRole": user.user_role,
                "createTime": user.create_time.isoformat() if user.create_time else None,
                "updateTime": user.update_time.isoformat() if user.update_time else None,
                "isDelete": user.is_delete,
            }
        )
    finally:
        db.close()


@router.get("/get/vo")
def get_user_vo(id: int, request: Request):
    db = next(_db(request))
    try:
        user = UserService(db).get_user(id)
        return success(UserService(db).to_user_vo(user))
    finally:
        db.close()


@router.post("/delete")
def delete_user(payload: DeleteRequest, request: Request, _=Depends(require_admin)):
    db = next(_db(request))
    try:
        return success(UserService(db).delete_user(payload.id))
    finally:
        db.close()


@router.post("/update")
def update_user(payload: UserUpdateRequest, request: Request, _=Depends(require_admin)):
    db = next(_db(request))
    try:
        return success(UserService(db).update_user(payload))
    finally:
        db.close()


@router.post("/list/page/vo")
def list_user_vo_by_page(payload: UserQueryRequest, request: Request, _=Depends(require_admin)):
    db = next(_db(request))
    try:
        records, total = UserService(db).list_user_vo_by_page(payload)
        return success(build_page(records, payload.pageNum, payload.pageSize, total))
    finally:
        db.close()
