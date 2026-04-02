from __future__ import annotations

import re
from pathlib import Path

from app.core.exceptions import BusinessException, ErrorCode

HTML_PATTERN = re.compile(r"```html\s*\n([\s\S]*?)```", re.IGNORECASE)
CSS_PATTERN = re.compile(r"```css\s*\n([\s\S]*?)```", re.IGNORECASE)
JS_PATTERN = re.compile(r"```(?:js|javascript)\s*\n([\s\S]*?)```", re.IGNORECASE)
VUE_FILE_PATTERN = re.compile(
    r"FILE:\s*(?P<path>[^\r\n]+)\r?\n```[^\n]*\n(?P<content>[\s\S]*?)```",
    re.IGNORECASE,
)


def extract_html(content: str) -> str:
    match = HTML_PATTERN.search(content)
    if match:
        return match.group(1).strip()
    return content.strip()


def extract_multi_file(content: str) -> dict[str, str]:
    html_match = HTML_PATTERN.search(content)
    css_match = CSS_PATTERN.search(content)
    js_match = JS_PATTERN.search(content)
    if not html_match:
        raise BusinessException(ErrorCode.SYSTEM_ERROR, "multi_file 模式缺少 html 代码块")
    return {
        "index.html": html_match.group(1).strip(),
        "style.css": css_match.group(1).strip() if css_match else "",
        "script.js": js_match.group(1).strip() if js_match else "",
    }


def extract_vue_project_files(content: str) -> dict[str, str]:
    files: dict[str, str] = {}
    for match in VUE_FILE_PATTERN.finditer(content):
        relative_path = match.group("path").strip().replace("\\", "/")
        normalized = Path(relative_path)
        if normalized.is_absolute() or ".." in normalized.parts:
            raise BusinessException(ErrorCode.SYSTEM_ERROR, f"非法文件路径: {relative_path}")
        files[relative_path] = match.group("content").strip()
    if not files:
        raise BusinessException(ErrorCode.SYSTEM_ERROR, "vue_project 模式未解析出任何文件")
    has_source_file = any(
        relative_path == "src/App.vue" or relative_path.startswith(("src/components/", "src/views/", "src/pages/"))
        for relative_path in files
    )
    if not has_source_file:
        raise BusinessException(
            ErrorCode.SYSTEM_ERROR,
            "vue_project 模式至少需要提供 src/App.vue、src/components/*、src/views/* 或 src/pages/* 之一",
        )
    return files
