from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from app.core.response import error_response

router = APIRouter(prefix="/static", tags=["static"])


def _content_type(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".html":
        return "text/html; charset=UTF-8"
    if suffix == ".css":
        return "text/css; charset=UTF-8"
    if suffix == ".js":
        return "application/javascript; charset=UTF-8"
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".svg":
        return "image/svg+xml"
    return "application/octet-stream"


@router.get("/{deploy_key}/")
def serve_static_root(deploy_key: str, request: Request):
    file_path = request.app.state.settings.code_output_root / deploy_key / "index.html"
    if not file_path.exists():
        return error_response(40400, "请求数据不存在")
    return FileResponse(file_path, media_type=_content_type(file_path))


@router.get("/covers/{file_name}")
def serve_cover_image(file_name: str, request: Request):
    file_path = request.app.state.settings.screenshot_root / file_name
    if not file_path.exists():
        return error_response(40400, "请求数据不存在")
    return FileResponse(file_path, media_type=_content_type(file_path))


@router.get("/{deploy_key}/{resource_path:path}")
def serve_static_resource(deploy_key: str, resource_path: str, request: Request):
    normalized_path = Path(resource_path or "index.html")
    file_path = request.app.state.settings.code_output_root / deploy_key / normalized_path
    if file_path.is_dir():
        file_path = file_path / "index.html"
    if not file_path.exists():
        return error_response(40400, "请求数据不存在")
    return FileResponse(file_path, media_type=_content_type(file_path))
