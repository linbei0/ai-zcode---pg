from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routers import (
    app_router,
    chat_history_router,
    health_router,
    static_router,
    user_router,
    workflow_router,
)
from app.core.config import Settings, build_settings
from app.core.database import build_session_factory, init_database
from app.core.exceptions import BusinessException
from app.core.response import error_response
from app.core.sessions import InMemorySessionStore, RedisSessionStore
from app.services.ai_service import build_ai_gateway


def create_app(overrides: dict[str, Any] | Settings | None = None) -> FastAPI:
    settings = overrides if isinstance(overrides, Settings) else build_settings(overrides)
    session_factory = build_session_factory(settings)
    init_database(session_factory)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings.code_output_root.mkdir(parents=True, exist_ok=True)
        settings.code_deploy_root.mkdir(parents=True, exist_ok=True)
        yield

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.session_store = InMemorySessionStore() if settings.testing else RedisSessionStore(settings.redis_url)
    app.state.ai_gateway = build_ai_gateway(settings)

    @app.exception_handler(BusinessException)
    async def handle_business_exception(_, exc: BusinessException):
        return JSONResponse(error_response(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(_, exc: RequestValidationError):
        return JSONResponse(error_response(40000, str(exc).split("\n", 1)[0]))

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(user_router, prefix=settings.api_prefix)
    app.include_router(app_router, prefix=settings.api_prefix)
    app.include_router(chat_history_router, prefix=settings.api_prefix)
    app.include_router(static_router, prefix=settings.api_prefix)
    app.include_router(workflow_router, prefix=settings.api_prefix)

    return app


app = create_app()
