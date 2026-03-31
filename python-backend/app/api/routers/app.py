from __future__ import annotations

import json
from collections.abc import AsyncIterable

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.database import db_session_dependency
from app.core.dependencies import get_current_user, require_admin
from app.core.exceptions import BusinessException, ErrorCode
from app.core.response import build_page, success
from app.schemas.app import (
    AppAddRequest,
    AppAdminUpdateRequest,
    AppDeployRequest,
    AppQueryRequest,
    AppUpdateRequest,
)
from app.schemas.common import DeleteRequest
from app.services.app_service import AppService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/app", tags=["app"])


def _db(request: Request):
    yield from db_session_dependency(request.app.state.session_factory)


def _service(request: Request, db) -> AppService:
    return AppService(db, request.app.state.ai_gateway, StorageService(request.app.state.settings))


@router.post("/add")
def add_app(payload: AppAddRequest, request: Request, _=Depends(get_current_user)):
    db = next(_db(request))
    try:
        login_user = get_current_user(request)
        return success(_service(request, db).create_app(payload, login_user))
    finally:
        db.close()


@router.post("/update")
def update_app(payload: AppUpdateRequest, request: Request, _=Depends(get_current_user)):
    db = next(_db(request))
    try:
        login_user = get_current_user(request)
        return success(_service(request, db).update_app(payload, login_user))
    finally:
        db.close()


@router.post("/delete")
def delete_app(payload: DeleteRequest, request: Request, _=Depends(get_current_user)):
    db = next(_db(request))
    try:
        login_user = get_current_user(request)
        return success(_service(request, db).delete_app(payload.id, login_user))
    finally:
        db.close()


@router.get("/get/vo")
def get_app_vo(id: int, request: Request):
    db = next(_db(request))
    try:
        service = _service(request, db)
        return success(service.get_app_vo(service.get_app_entity(id)))
    finally:
        db.close()


@router.post("/my/list/page/vo")
def list_my_app_vo_by_page(payload: AppQueryRequest, request: Request, _=Depends(get_current_user)):
    if payload.pageSize > 20:
        raise BusinessException(ErrorCode.PARAMS_ERROR, "每页最多查询 20 个应用")
    db = next(_db(request))
    try:
        login_user = get_current_user(request)
        payload.userId = login_user.id
        records, total = _service(request, db).list_page(payload)
        return success(build_page(records, payload.pageNum, payload.pageSize, total))
    finally:
        db.close()


@router.post("/good/list/page/vo")
def list_good_app_vo_by_page(payload: AppQueryRequest, request: Request):
    if payload.pageSize > 20:
        raise BusinessException(ErrorCode.PARAMS_ERROR, "每页最多查询 20 个应用")
    db = next(_db(request))
    try:
        payload.priority = 99
        records, total = _service(request, db).list_page(payload)
        return success(build_page(records, payload.pageNum, payload.pageSize, total))
    finally:
        db.close()


@router.post("/admin/delete")
def delete_app_by_admin(payload: DeleteRequest, request: Request, _=Depends(require_admin)):
    db = next(_db(request))
    try:
        app = _service(request, db).get_app_entity(payload.id)
        app.is_delete = 1
        db.commit()
        return success(True)
    finally:
        db.close()


@router.post("/admin/update")
def update_app_by_admin(payload: AppAdminUpdateRequest, request: Request, _=Depends(require_admin)):
    db = next(_db(request))
    try:
        return success(_service(request, db).update_app_by_admin(payload))
    finally:
        db.close()


@router.post("/admin/list/page/vo")
def list_app_by_page_by_admin(payload: AppQueryRequest, request: Request, _=Depends(require_admin)):
    db = next(_db(request))
    try:
        records, total = _service(request, db).list_page(payload)
        return success(build_page(records, payload.pageNum, payload.pageSize, total))
    finally:
        db.close()


@router.get("/admin/get/vo")
def get_app_vo_by_admin(id: int, request: Request, _=Depends(require_admin)):
    db = next(_db(request))
    try:
        service = _service(request, db)
        return success(service.get_app_vo(service.get_app_entity(id)))
    finally:
        db.close()


@router.get("/chat/gen/code")
async def chat_to_gen_code(appId: int, message: str, request: Request, _=Depends(get_current_user)):
    if appId <= 0:
        raise BusinessException(ErrorCode.PARAMS_ERROR, "应用ID无效")
    if not message.strip():
        raise BusinessException(ErrorCode.PARAMS_ERROR, "用户消息不能为空")
    db = next(_db(request))
    login_user = get_current_user(request)
    service = _service(request, db)

    async def event_generator() -> AsyncIterable[str]:
        try:
            async for chunk in service.chat_to_generate_code(appId, message, login_user):
                payload = json.dumps({"d": chunk}, ensure_ascii=False, separators=(",", ":"))
                yield f"data: {payload}\n\n"
            yield "event: done\ndata:\n\n"
        except BusinessException as exc:
            payload = json.dumps(
                {"code": exc.code, "message": exc.message},
                ensure_ascii=False,
                separators=(",", ":"),
            )
            yield f"event: business-error\ndata: {payload}\n\n"
        finally:
            db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/deploy")
def deploy_app(payload: AppDeployRequest, request: Request, _=Depends(get_current_user)):
    db = next(_db(request))
    try:
        login_user = get_current_user(request)
        settings = request.app.state.settings
        return success(_service(request, db).deploy_app(payload.appId, login_user, settings.code_deploy_host))
    finally:
        db.close()


@router.get("/download/{app_id}")
def download_app_code(app_id: int, request: Request, _=Depends(get_current_user)):
    db = next(_db(request))
    try:
        login_user = get_current_user(request)
        data = _service(request, db).build_download_zip(app_id, login_user)
        headers = {"Content-Disposition": f'attachment; filename="{app_id}.zip"'}
        return StreamingResponse(iter([data]), media_type="application/zip", headers=headers)
    finally:
        db.close()
