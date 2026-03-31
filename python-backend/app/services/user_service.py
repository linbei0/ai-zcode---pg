from __future__ import annotations

from datetime import UTC, datetime
from hashlib import md5

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessException, ErrorCode
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserAddRequest, UserQueryRequest, UserUpdateRequest


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)

    def register(self, user_account: str, user_password: str, check_password: str) -> int:
        if not user_account or not user_password or not check_password:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "参数为空")
        if len(user_account) < 4:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "用户账号过短")
        if len(user_password) < 8 or len(check_password) < 8:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "用户密码过短")
        if user_password != check_password:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "两次输入的密码不一致")
        if self.repository.get_by_account(user_account):
            raise BusinessException(ErrorCode.PARAMS_ERROR, "账号重复")

        user = User(
            user_account=user_account,
            user_password=self.get_encrypt_password(user_password),
            user_name="无名",
            user_role="user",
            edit_time=datetime.now(UTC),
        )
        self.repository.save(user)
        self.db.commit()
        return user.id

    def login(self, user_account: str, user_password: str) -> User:
        if not user_account or not user_password:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "参数为空")
        if len(user_account) < 4:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "账号错误")
        if len(user_password) < 8:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "密码错误")

        encrypted = self.get_encrypt_password(user_password)
        stmt = select(User).where(
            User.user_account == user_account,
            User.user_password == encrypted,
            User.is_delete == 0,
        )
        user = self.db.execute(stmt).scalar_one_or_none()
        if not user:
            raise BusinessException(ErrorCode.PARAMS_ERROR, "用户不存在或密码错误")
        return user

    def add_user(self, payload: UserAddRequest) -> int:
        if self.repository.get_by_account(payload.userAccount):
            raise BusinessException(ErrorCode.PARAMS_ERROR, "账号重复")
        user = User(
            user_name=payload.userName,
            user_account=payload.userAccount,
            user_avatar=payload.userAvatar,
            user_profile=payload.userProfile,
            user_role=payload.userRole or "user",
            user_password=self.get_encrypt_password("password123"),
            edit_time=datetime.now(UTC),
        )
        self.repository.save(user)
        self.db.commit()
        return user.id

    def update_user(self, payload: UserUpdateRequest) -> bool:
        user = self.repository.get_by_id(payload.id)
        if not user or user.is_delete:
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR)
        user.user_name = payload.userName
        user.user_avatar = payload.userAvatar
        user.user_profile = payload.userProfile
        if payload.userRole:
            user.user_role = payload.userRole
        user.edit_time = datetime.now(UTC)
        self.db.commit()
        return True

    def delete_user(self, user_id: int) -> bool:
        user = self.repository.get_by_id(user_id)
        if not user or user.is_delete:
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR)
        user.is_delete = 1
        self.db.commit()
        return True

    def get_user(self, user_id: int) -> User:
        user = self.repository.get_by_id(user_id)
        if not user or user.is_delete:
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR)
        return user

    def list_user_vo_by_page(self, query: UserQueryRequest) -> tuple[list[dict], int]:
        stmt = select(User).where(User.is_delete == 0)
        count_stmt = select(func.count(User.id)).where(User.is_delete == 0)
        if query.id:
            stmt = stmt.where(User.id == query.id)
            count_stmt = count_stmt.where(User.id == query.id)
        if query.userRole:
            stmt = stmt.where(User.user_role == query.userRole)
            count_stmt = count_stmt.where(User.user_role == query.userRole)
        if query.userAccount:
            stmt = stmt.where(User.user_account.like(f"%{query.userAccount}%"))
            count_stmt = count_stmt.where(User.user_account.like(f"%{query.userAccount}%"))
        if query.userName:
            stmt = stmt.where(User.user_name.like(f"%{query.userName}%"))
            count_stmt = count_stmt.where(User.user_name.like(f"%{query.userName}%"))
        if query.userProfile:
            stmt = stmt.where(User.user_profile.like(f"%{query.userProfile}%"))
            count_stmt = count_stmt.where(User.user_profile.like(f"%{query.userProfile}%"))

        stmt = self._apply_sort(stmt, query.sortField, query.sortOrder, User.id)
        total = self.db.execute(count_stmt).scalar_one()
        offset = (query.pageNum - 1) * query.pageSize
        records = self.db.execute(stmt.offset(offset).limit(query.pageSize)).scalars().all()
        return [self.to_user_vo(item) for item in records], total

    def to_login_user_vo(self, user: User) -> dict:
        return {
            "id": user.id,
            "userAccount": user.user_account,
            "userName": user.user_name,
            "userAvatar": user.user_avatar,
            "userProfile": user.user_profile,
            "userRole": user.user_role,
            "createTime": user.create_time.isoformat() if user.create_time else None,
            "updateTime": user.update_time.isoformat() if user.update_time else None,
        }

    def to_user_vo(self, user: User) -> dict:
        return {
            "id": user.id,
            "userAccount": user.user_account,
            "userName": user.user_name,
            "userAvatar": user.user_avatar,
            "userProfile": user.user_profile,
            "userRole": user.user_role,
            "createTime": user.create_time.isoformat() if user.create_time else None,
        }

    def get_encrypt_password(self, user_password: str) -> str:
        return md5(f"aizcode{user_password}".encode("utf-8")).hexdigest()

    def _apply_sort(self, stmt, sort_field: str | None, sort_order: str | None, default_column):
        sort_mapping = {
            "id": User.id,
            "create_time": User.create_time,
            "update_time": User.update_time,
        }
        column = sort_mapping.get(sort_field or "", default_column)
        if sort_order in {"asc", "ascend"}:
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())
