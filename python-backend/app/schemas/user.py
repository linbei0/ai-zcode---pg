from __future__ import annotations

from pydantic import BaseModel


class UserRegisterRequest(BaseModel):
    userAccount: str
    userPassword: str
    checkPassword: str


class UserLoginRequest(BaseModel):
    userAccount: str
    userPassword: str


class UserAddRequest(BaseModel):
    userName: str | None = None
    userAccount: str
    userAvatar: str | None = None
    userProfile: str | None = None
    userRole: str | None = "user"


class UserUpdateRequest(BaseModel):
    id: int
    userName: str | None = None
    userAvatar: str | None = None
    userProfile: str | None = None
    userRole: str | None = None


class UserQueryRequest(BaseModel):
    pageNum: int = 1
    pageSize: int = 10
    sortField: str | None = None
    sortOrder: str | None = "descend"
    id: int | None = None
    userName: str | None = None
    userAccount: str | None = None
    userProfile: str | None = None
    userRole: str | None = None
