from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod

from app.core.config import Settings

logger = logging.getLogger(__name__)


class ScreenshotService(ABC):
    @abstractmethod
    def generate_screenshot(self, web_url: str) -> str | None: ...


class TestingScreenshotService(ScreenshotService):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.screenshot_root.mkdir(parents=True, exist_ok=True)

    def generate_screenshot(self, web_url: str) -> str | None:
        file_name = f"{uuid.uuid4().hex[:8]}.svg"
        file_path = self.settings.screenshot_root / file_name
        file_path.write_text(self._build_svg(web_url), encoding="utf-8")
        return f"{self.settings.public_api_base_url}/static/covers/{file_name}"

    def _build_svg(self, web_url: str) -> str:
        safe_url = web_url.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#4facfe"/>
      <stop offset="100%" stop-color="#00f2fe"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect x="60" y="60" width="1080" height="510" rx="28" fill="rgba(255,255,255,0.92)"/>
  <text x="110" y="180" font-size="52" font-family="Arial, sans-serif" font-weight="700" fill="#0f172a">AI-ZCode Deploy Cover</text>
  <text x="110" y="260" font-size="28" font-family="Arial, sans-serif" fill="#334155">自动生成的部署封面</text>
  <text x="110" y="340" font-size="24" font-family="Arial, sans-serif" fill="#1e293b">{safe_url}</text>
</svg>"""


class PlaywrightScreenshotService(ScreenshotService):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.screenshot_root.mkdir(parents=True, exist_ok=True)

    def generate_screenshot(self, web_url: str) -> str | None:
        file_name = f"{uuid.uuid4().hex[:8]}.svg"
        file_path = self.settings.screenshot_root / file_name
        try:
            file_path.write_text(TestingScreenshotService(self.settings)._build_svg(web_url), encoding="utf-8")
            logger.info("已生成部署封面资源（SVG）: %s", file_path)
            return f"{self.settings.public_api_base_url}/static/covers/{file_name}"
        except Exception as exc:
            logger.error("生成部署封面资源失败: %s", exc, exc_info=True)
            return None


def build_screenshot_service(settings: Settings) -> ScreenshotService:
    if settings.testing:
        return TestingScreenshotService(settings)
    return PlaywrightScreenshotService(settings)
