from __future__ import annotations

from collections.abc import AsyncIterable

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.database import db_session_dependency
from app.core.dependencies import get_current_user
from app.core.exceptions import BusinessException, ErrorCode
from app.core.response import success
from app.services.storage_service import StorageService
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflow", tags=["workflow"])


def _db(request: Request):
    yield from db_session_dependency(request.app.state.session_factory)


def _workflow_service(request: Request) -> WorkflowService:
    return WorkflowService(
        request.app.state.ai_gateway,
        StorageService(request.app.state.settings),
    )


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


@router.post("/execute")
async def execute_workflow(prompt: str, request: Request):
    return await _workflow_service(request).execute(prompt)


@router.get("/execute-flux")
async def execute_workflow_with_flux(prompt: str, request: Request):
    async def generator() -> AsyncIterable[str]:
        async for item in _workflow_service(request).execute_flux(prompt):
            yield item

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/execute-sse")
async def execute_workflow_with_sse(prompt: str, request: Request):
    async def generator() -> AsyncIterable[str]:
        async for item in _workflow_service(request).execute_sse(prompt):
            yield item

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
