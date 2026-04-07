from __future__ import annotations

import base64
import logging
import shutil
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from app.core.config import Settings

logger = logging.getLogger(__name__)

_TEST_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9p2vNh8AAAAASUVORK5CYII="
)


class ScreenshotService(ABC):
    @abstractmethod
    def generate_screenshot(self, web_url: str, app_id: int | None = None) -> str | None: ...


class ScreenshotRenderer(ABC):
    @abstractmethod
    def render(self, web_url: str, output_path: Path) -> Path: ...


class ScreenshotUploader(ABC):
    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def upload_file(self, local_path: Path) -> str: ...


class TestingScreenshotRenderer(ScreenshotRenderer):
    def render(self, web_url: str, output_path: Path) -> Path:
        output_path.write_bytes(_TEST_PNG_BYTES)
        return output_path


class PlaywrightScreenshotRenderer(ScreenshotRenderer):
    def __init__(self, settings: Settings):
        self.settings = settings

    def render(self, web_url: str, output_path: Path) -> Path:
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright 未安装，请先执行 `playwright install chromium`") from exc

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(
                viewport={
                    "width": self.settings.screenshot_width,
                    "height": self.settings.screenshot_height,
                }
            )
            try:
                page.goto(web_url, wait_until="load", timeout=self.settings.screenshot_timeout_seconds * 1000)
                try:
                    page.wait_for_load_state(
                        "networkidle",
                        timeout=min(self.settings.screenshot_timeout_seconds * 1000, 5000),
                    )
                except PlaywrightTimeoutError:
                    logger.warning("截图等待 networkidle 超时，继续截图: %s", web_url)
                page.screenshot(path=str(output_path), full_page=True)
                return output_path
            finally:
                browser.close()


class TestingScreenshotUploader(ScreenshotUploader):
    def __init__(self, settings: Settings):
        self.settings = settings

    def is_available(self) -> bool:
        return True

    def upload_file(self, local_path: Path) -> str:
        key = CosScreenshotUploader(self.settings).build_object_key(local_path.name)
        base_url = (self.settings.cos_host or "https://cos.example.com").rstrip("/")
        return f"{base_url}/{quote(key.lstrip('/'))}".replace("%2F", "/")


class CosScreenshotUploader(ScreenshotUploader):
    def __init__(self, settings: Settings):
        self.settings = settings

    def is_available(self) -> bool:
        return all(
            [
                self.settings.cos_secret_id,
                self.settings.cos_secret_key,
                self.settings.cos_region,
                self.settings.cos_bucket,
                self.settings.cos_host,
            ]
        )

    def build_object_key(self, file_name: str) -> str:
        date_path = datetime.now(UTC).strftime("%Y/%m/%d")
        return f"/screenshots/{date_path}/{file_name}"

    def upload_file(self, local_path: Path) -> str:
        if not self.is_available():
            raise RuntimeError("COS 配置不完整，无法上传截图")
        try:
            import qcloud_cos
        except ImportError as exc:
            raise RuntimeError("qcloud COS SDK 未安装，请安装 cos-python-sdk-v5") from exc

        key = self.build_object_key(local_path.name)
        self._upload_with_sdk(qcloud_cos, local_path, key)
        return f"{self.settings.cos_host.rstrip('/')}/{quote(key.lstrip('/'))}".replace("%2F", "/")

    def _upload_with_sdk(self, sdk_module, local_path: Path, key: str) -> None:
        cos_s3_client = getattr(sdk_module, "CosS3Client", None)
        cos_config = getattr(sdk_module, "CosConfig", None)
        if cos_s3_client and cos_config:
            config = cos_config(
                Region=self.settings.cos_region,
                SecretId=self.settings.cos_secret_id,
                SecretKey=self.settings.cos_secret_key,
            )
            client = cos_s3_client(config)
            with local_path.open("rb") as file_obj:
                response = client.put_object(
                    Bucket=self.settings.cos_bucket,
                    Body=file_obj,
                    Key=key,
                    EnableMD5=False,
                )
            if not response:
                raise RuntimeError("COS 上传失败：SDK 未返回结果")
            return
        raise RuntimeError("检测到旧版 qcloud_cos SDK，请卸载后安装 cos-python-sdk-v5")


class BaseScreenshotService(ScreenshotService):
    def __init__(self, settings: Settings, renderer: ScreenshotRenderer, uploader: ScreenshotUploader):
        self.settings = settings
        self.renderer = renderer
        self.uploader = uploader
        self.settings.screenshot_root.mkdir(parents=True, exist_ok=True)

    def generate_screenshot(self, web_url: str, app_id: int | None = None) -> str | None:
        if not web_url.strip():
            logger.error("截图任务参数非法，web_url 为空，app_id=%s", app_id)
            return None
        if not self.uploader.is_available():
            logger.warning("截图上传已跳过，COS 配置不完整，app_id=%s, url=%s", app_id, web_url)
            return None

        temp_dir = self.settings.screenshot_root / uuid.uuid4().hex[:8]
        temp_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = temp_dir / f"{uuid.uuid4().hex[:8]}.png"
        try:
            # 截图链路：渲染页面 -> 上传 COS -> 返回最终封面 URL。
            logger.info("开始生成应用截图，app_id=%s, url=%s", app_id, web_url)
            self.renderer.render(web_url, screenshot_path)
            logger.info("应用截图渲染完成，app_id=%s, path=%s", app_id, screenshot_path)
            cover_url = self.uploader.upload_file(screenshot_path)
            logger.info("应用截图上传完成，app_id=%s, cover=%s", app_id, cover_url)
            return cover_url
        except Exception as exc:
            logger.error("应用截图处理失败，app_id=%s, url=%s, error=%s", app_id, web_url, exc, exc_info=True)
            return None
        finally:
            # 无论成功还是失败都清理临时文件，避免截图目录无限增长。
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestingScreenshotService(BaseScreenshotService):
    __test__ = False

    def __init__(self, settings: Settings):
        super().__init__(
            settings=settings,
            renderer=TestingScreenshotRenderer(),
            uploader=TestingScreenshotUploader(settings),
        )
        self.should_fail = False

    def generate_screenshot(self, web_url: str, app_id: int | None = None) -> str | None:
        if self.should_fail:
            logger.error("测试截图服务已注入失败，app_id=%s, url=%s", app_id, web_url)
            return None
        return super().generate_screenshot(web_url, app_id)


class PlaywrightScreenshotService(BaseScreenshotService):
    def __init__(self, settings: Settings):
        super().__init__(
            settings=settings,
            renderer=PlaywrightScreenshotRenderer(settings),
            uploader=CosScreenshotUploader(settings),
        )


def build_screenshot_service(settings: Settings) -> ScreenshotService:
    if settings.testing:
        return TestingScreenshotService(settings)
    return PlaywrightScreenshotService(settings)
