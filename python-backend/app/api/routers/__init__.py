from app.api.routers.app import router as app_router
from app.api.routers.chat_history import router as chat_history_router
from app.api.routers.health import router as health_router
from app.api.routers.static_resource import router as static_router
from app.api.routers.user import router as user_router
from app.api.routers.workflow import router as workflow_router

__all__ = [
    "app_router",
    "chat_history_router",
    "health_router",
    "static_router",
    "user_router",
    "workflow_router",
]
