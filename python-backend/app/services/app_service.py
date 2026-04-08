from __future__ import annotations

import logging
import random
import string
import threading
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.cache import CacheStore
from app.core.exceptions import BusinessException, ErrorCode
from app.models.app import App
from app.models.user import User
from app.repositories.app_repository import AppRepository
from app.schemas.app import (
    AppAddRequest,
    AppAdminUpdateRequest,
    AppQueryRequest,
    AppUpdateRequest,
    PromptOptimizeRequest,
    PromptOptimizeResponse,
)
from app.services.ai_service import AIGateway
from app.services.chat_history_service import ChatHistoryService
from app.services.screenshot_service import ScreenshotService
from app.services.storage_service import StorageService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class AppService:
    def __init__(
        self,
        db: Session,
        ai_gateway: AIGateway,
        storage_service: StorageService,
        cache_store: CacheStore | None = None,
        screenshot_service: ScreenshotService | None = None,
        settings: Any | None = None,
        session_factory: Any | None = None,
    ):
        self.db = db
        self.repository = AppRepository(db)
        self.ai_gateway = ai_gateway
        self.storage_service = storage_service
        self.cache_store = cache_store
        self.screenshot_service = screenshot_service
        self.settings = settings
        self.session_factory = session_factory
        self.user_service = UserService(db)
        self.chat_history_service = ChatHistoryService(db)

    def create_app(self, payload: AppAddRequest, login_user: User) -> int:
        init_prompt = payload.initPrompt.strip() if payload.initPrompt else ""
        if not init_prompt:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "初始化 prompt 不能为空")
        code_gen_type = self.ai_gateway.route_code_type(init_prompt)
        app = App(
            app_name=init_prompt[:12],
            init_prompt=init_prompt,
            code_gen_type=code_gen_type,
            priority=0,
            user_id=login_user.id,
            edit_time=datetime.now(UTC),
        )
        self.repository.save(app)
        self.db.commit()
        self.invalidate_app_caches(app.id)
        return app.id

    def update_app(self, payload: AppUpdateRequest, login_user: User) -> bool:
        app = self.get_app_entity(payload.id)
        if app.user_id != login_user.id:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR)
        app.app_name = payload.appName
        app.edit_time = datetime.now(UTC)
        self.db.commit()
        self.invalidate_app_caches(app.id)
        return True

    def delete_app(self, app_id: int, login_user: User) -> bool:
        app = self.get_app_entity(app_id)
        if app.user_id != login_user.id and login_user.user_role != "admin":
            raise BusinessException(ErrorCode.NO_AUTH_ERROR)
        app.is_delete = 1
        self.db.commit()
        self.invalidate_app_caches(app.id)
        return True

    def get_app_entity(self, app_id: int) -> App:
        app = self.repository.get_by_id(app_id)
        if not app:
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "应用不存在")
        return app

    def get_app_vo(self, app: App) -> dict[str, Any]:
        cache_key = self._app_vo_cache_key(app.id)
        if self.cache_store:
            cached = self.cache_store.get_json(cache_key)
            if cached:
                return cached
        user = self.user_service.get_user(app.user_id)
        payload = {
            "id": app.id,
            "appName": app.app_name,
            "cover": app.cover,
            "initPrompt": app.init_prompt,
            "codeGenType": app.code_gen_type,
            "deployKey": app.deploy_key,
            "deployedTime": app.deployed_time.isoformat() if app.deployed_time else None,
            "priority": app.priority,
            "userId": app.user_id,
            "createTime": app.create_time.isoformat() if app.create_time else None,
            "updateTime": app.update_time.isoformat() if app.update_time else None,
            "user": self.user_service.to_user_vo(user),
        }
        if self.cache_store and self.settings:
            self.cache_store.set_json(cache_key, payload, self.settings.app_vo_cache_ttl_seconds)
        return payload

    def list_page(self, query: AppQueryRequest) -> tuple[list[dict], int]:
        cache_key = None
        if self.cache_store and self.settings and query.priority == 99 and query.pageNum <= 10:
            cache_key = self._good_app_cache_key(query)
            cached = self.cache_store.get_json(cache_key)
            if cached:
                return cached["records"], cached["total"]
        stmt = select(App).where(App.is_delete == 0)
        count_stmt = select(func.count(App.id)).where(App.is_delete == 0)
        if query.id:
            stmt = stmt.where(App.id == query.id)
            count_stmt = count_stmt.where(App.id == query.id)
        if query.appName:
            stmt = stmt.where(App.app_name.like(f"%{query.appName}%"))
            count_stmt = count_stmt.where(App.app_name.like(f"%{query.appName}%"))
        if query.cover:
            stmt = stmt.where(App.cover.like(f"%{query.cover}%"))
            count_stmt = count_stmt.where(App.cover.like(f"%{query.cover}%"))
        if query.initPrompt:
            stmt = stmt.where(App.init_prompt.like(f"%{query.initPrompt}%"))
            count_stmt = count_stmt.where(App.init_prompt.like(f"%{query.initPrompt}%"))
        if query.codeGenType:
            stmt = stmt.where(App.code_gen_type == query.codeGenType)
            count_stmt = count_stmt.where(App.code_gen_type == query.codeGenType)
        if query.deployKey:
            stmt = stmt.where(App.deploy_key == query.deployKey)
            count_stmt = count_stmt.where(App.deploy_key == query.deployKey)
        if query.priority is not None:
            stmt = stmt.where(App.priority == query.priority)
            count_stmt = count_stmt.where(App.priority == query.priority)
        if query.userId:
            stmt = stmt.where(App.user_id == query.userId)
            count_stmt = count_stmt.where(App.user_id == query.userId)

        stmt = self._apply_sort(stmt, query.sortField, query.sortOrder)
        total = self.db.execute(count_stmt).scalar_one()
        offset = (query.pageNum - 1) * query.pageSize
        records = self.db.execute(stmt.offset(offset).limit(query.pageSize)).scalars().all()
        payload = [self.get_app_vo(item) for item in records]
        if cache_key and self.cache_store and self.settings:
            self.cache_store.set_json(cache_key, {"records": payload, "total": total}, self.settings.good_app_cache_ttl_seconds)
        return payload, total

    def optimize_prompt(self, payload: PromptOptimizeRequest, login_user: User) -> PromptOptimizeResponse:
        normalized_prompt = payload.prompt.strip() if payload.prompt else ""
        if not normalized_prompt:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "提示词不能为空")

        app_context: dict[str, Any] | None = None
        if payload.scene == "chat":
            if not payload.appId or payload.appId <= 0:
                raise BusinessException(ErrorCode.PARAMS_ERROR, "聊天场景必须提供有效的应用 ID")
            app = self.get_app_entity(payload.appId)
            if app.user_id != login_user.id:
                raise BusinessException(ErrorCode.NO_AUTH_ERROR, "无权限优化该应用的提示词")
            app_context = {
                "appName": app.app_name,
                "initPrompt": app.init_prompt,
                "codeGenType": app.code_gen_type,
            }

        result = self.ai_gateway.optimize_prompt(normalized_prompt, payload.scene, app_context)
        optimized_prompt = result["optimizedPrompt"].strip()
        if not optimized_prompt:
            raise BusinessException(ErrorCode.SYSTEM_ERROR, "提示词优化失败，请稍后重试")
        return PromptOptimizeResponse(optimizedPrompt=optimized_prompt, mode=result["mode"])

    async def chat_to_generate_code(self, app_id: int, message: str, login_user: User):
        if app_id <= 0:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "应用 ID 不能为空")
        if not message.strip():
            raise BusinessException(ErrorCode.PARAMS_ERROR, "用户消息不能为空")
        app = self.get_app_entity(app_id)
        if app.user_id != login_user.id:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "无权限访问该应用")

        self.chat_history_service.add_chat_message(app_id, message, "user", login_user.id)
        history_text = self.chat_history_service.build_history_text(app_id)

        chunks: list[str] = []
        try:
            async for chunk in self.ai_gateway.stream_generate(app.code_gen_type, message, history_text):
                chunks.append(chunk)
                yield chunk
        except Exception as exc:
            error_message = f"AI回复失败: {exc}"
            self.chat_history_service.add_chat_message(app_id, error_message, "ai", login_user.id)
            if isinstance(exc, BusinessException):
                raise
            raise BusinessException(ErrorCode.SYSTEM_ERROR, str(exc)) from exc

        full_content = "".join(chunks)
        try:
            source_dir = self.storage_service.save_generated_code(app.code_gen_type, app_id, full_content)
            # Vue 项目需要先同步构建 dist，前端预览才能访问到 dist/index.html
            self.storage_service.build_vue_project_if_needed(app.code_gen_type, source_dir)
            self.chat_history_service.add_chat_message(app_id, full_content, "ai", login_user.id)
        except Exception as exc:
            error_message = f"代码保存或构建失败: {exc}"
            self.chat_history_service.add_chat_message(app_id, error_message, "ai", login_user.id)
            if isinstance(exc, BusinessException):
                raise
            raise BusinessException(ErrorCode.SYSTEM_ERROR, str(exc)) from exc

    def deploy_app(self, app_id: int, login_user: User, code_deploy_host: str) -> str:
        app = self.get_app_entity(app_id)
        if app.user_id != login_user.id:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "无权限部署该应用")
        deploy_key = app.deploy_key or self._generate_deploy_key()
        deploy_url = self.storage_service.deploy(app.code_gen_type, app_id, deploy_key)
        app.deploy_key = deploy_key
        app.deployed_time = datetime.now(UTC)
        self.db.commit()
        self.invalidate_app_caches(app.id)
        self.generate_app_cover(app.id, deploy_url.replace("http://localhost", code_deploy_host, 1))
        return deploy_url.replace("http://localhost", code_deploy_host, 1)

    def build_download_zip(self, app_id: int, login_user: User) -> bytes:
        app = self.get_app_entity(app_id)
        if app.user_id != login_user.id:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "无权限下载该应用代码")
        return self.storage_service.build_download_zip(app.code_gen_type, app_id)

    def update_app_by_admin(self, payload: AppAdminUpdateRequest) -> bool:
        app = self.get_app_entity(payload.id)
        if payload.appName is not None:
            app.app_name = payload.appName
        if payload.cover is not None:
            app.cover = payload.cover
        if payload.priority is not None:
            app.priority = payload.priority
        app.edit_time = datetime.now(UTC)
        self.db.commit()
        self.invalidate_app_caches(app.id)
        return True

    def generate_app_cover(self, app_id: int, app_url: str) -> None:
        if not self.screenshot_service or not self.session_factory:
            return

        def run_cover_job() -> None:
            cover_url = self.screenshot_service.generate_screenshot(app_url, app_id=app_id)
            if not cover_url:
                return
            db = self.session_factory()
            try:
                app = db.get(App, app_id)
                if app and app.is_delete == 0:
                    app.cover = cover_url
                    db.commit()
                    if self.cache_store:
                        self.invalidate_app_caches(app_id)
            except Exception as exc:
                logger.error("回写应用封面失败，app_id=%s, cover=%s, error=%s", app_id, cover_url, exc, exc_info=True)
            finally:
                db.close()

        threading.Thread(target=run_cover_job, name=f"app-cover-{app_id}", daemon=True).start()

    def invalidate_app_caches(self, app_id: int) -> None:
        if not self.cache_store:
            return
        self.cache_store.delete(self._app_vo_cache_key(app_id))
        self.cache_store.delete_prefix("good_app_page:")

    def _good_app_cache_key(self, query: AppQueryRequest) -> str:
        return (
            "good_app_page:"
            f"page={query.pageNum}:size={query.pageSize}:sort={query.sortField or ''}:order={query.sortOrder or ''}"
        )

    def _app_vo_cache_key(self, app_id: int) -> str:
        return f"app_vo:{app_id}"

    def _apply_sort(self, stmt, sort_field: str | None, sort_order: str | None):
        mapping = {
            "id": App.id,
            "create_time": App.create_time,
            "update_time": App.update_time,
            "priority": App.priority,
        }
        column = mapping.get(sort_field or "", App.id)
        if sort_order in {"asc", "ascend"}:
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())

    def _generate_deploy_key(self) -> str:
        while True:
            deploy_key = "".join(random.choices(string.ascii_letters + string.digits, k=6))
            exists = self.db.execute(select(App.id).where(App.deploy_key == deploy_key)).scalar_one_or_none()
            if not exists:
                return deploy_key
