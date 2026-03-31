from __future__ import annotations

import random
import string
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException, ErrorCode
from app.models.app import App
from app.models.user import User
from app.repositories.app_repository import AppRepository
from app.schemas.app import AppAddRequest, AppAdminUpdateRequest, AppQueryRequest, AppUpdateRequest
from app.services.ai_service import AIGateway
from app.services.chat_history_service import ChatHistoryService
from app.services.storage_service import StorageService
from app.services.user_service import UserService


class AppService:
    def __init__(self, db: Session, ai_gateway: AIGateway, storage_service: StorageService):
        self.db = db
        self.repository = AppRepository(db)
        self.ai_gateway = ai_gateway
        self.storage_service = storage_service
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
        return app.id

    def update_app(self, payload: AppUpdateRequest, login_user: User) -> bool:
        app = self.get_app_entity(payload.id)
        if app.user_id != login_user.id:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR)
        app.app_name = payload.appName
        app.edit_time = datetime.now(UTC)
        self.db.commit()
        return True

    def delete_app(self, app_id: int, login_user: User) -> bool:
        app = self.get_app_entity(app_id)
        if app.user_id != login_user.id and login_user.user_role != "admin":
            raise BusinessException(ErrorCode.NO_AUTH_ERROR)
        app.is_delete = 1
        self.db.commit()
        return True

    def get_app_entity(self, app_id: int) -> App:
        app = self.repository.get_by_id(app_id)
        if not app:
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "应用不存在")
        return app

    def get_app_vo(self, app: App) -> dict[str, Any]:
        user = self.user_service.get_user(app.user_id)
        return {
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

    def list_page(self, query: AppQueryRequest) -> tuple[list[dict], int]:
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
        return [self.get_app_vo(item) for item in records], total

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
        self.storage_service.save_generated_code(app.code_gen_type, app_id, full_content)
        self.chat_history_service.add_chat_message(app_id, full_content, "ai", login_user.id)

    def deploy_app(self, app_id: int, login_user: User, code_deploy_host: str) -> str:
        app = self.get_app_entity(app_id)
        if app.user_id != login_user.id:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "无权限部署该应用")
        deploy_key = app.deploy_key or self._generate_deploy_key()
        deploy_url = self.storage_service.deploy(app.code_gen_type, app_id, deploy_key)
        app.deploy_key = deploy_key
        app.deployed_time = datetime.now(UTC)
        self.db.commit()
        return deploy_url.replace("http://localhost", code_deploy_host, 1)

    def build_download_zip(self, app_id: int, login_user: User) -> bytes:
        app = self.get_app_entity(app_id)
        if app.user_id != login_user.id:
            raise BusinessException(ErrorCode.NO_AUTH_ERROR, "无权限下载该应用代码")
        return self.storage_service.build_download_zip(app.code_gen_type, app_id)

    def update_app_by_admin(self, payload: AppAdminUpdateRequest) -> bool:
        app = self.get_app_entity(payload.id)
        app.app_name = payload.appName
        app.cover = payload.cover
        if payload.priority is not None:
            app.priority = payload.priority
        app.edit_time = datetime.now(UTC)
        self.db.commit()
        return True

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
