from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

PromptOptimizeScene = Literal["create_app", "chat"]
PromptOptimizeMode = Literal["basic", "detail"]


class AppAddRequest(BaseModel):
    initPrompt: str


class AppUpdateRequest(BaseModel):
    id: int
    appName: str | None = None


class AppAdminUpdateRequest(BaseModel):
    id: int
    appName: str | None = None
    cover: str | None = None
    priority: int | None = None


class AppQueryRequest(BaseModel):
    pageNum: int = 1
    pageSize: int = 10
    sortField: str | None = None
    sortOrder: str | None = "descend"
    id: int | None = None
    appName: str | None = None
    cover: str | None = None
    initPrompt: str | None = None
    codeGenType: str | None = None
    deployKey: str | None = None
    priority: int | None = None
    userId: int | None = None


class AppDeployRequest(BaseModel):
    appId: int


class PromptOptimizeRequest(BaseModel):
    prompt: str
    scene: PromptOptimizeScene
    appId: int | None = None


class PromptOptimizeResponse(BaseModel):
    optimizedPrompt: str
    mode: PromptOptimizeMode
