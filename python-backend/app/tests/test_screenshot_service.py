from pathlib import Path
from types import SimpleNamespace

from app.core.config import build_settings
from app.services.screenshot_service import (
    CosScreenshotUploader,
    TestingScreenshotService,
)


def test_testing_screenshot_service_returns_cos_style_url_and_cleans_temp_file(tmp_path: Path) -> None:
    settings = build_settings(
        {
            "testing": True,
            "repo_root": str(tmp_path),
            "cos_secret_id": "test-secret-id",
            "cos_secret_key": "test-secret-key",
            "cos_region": "ap-shanghai",
            "cos_bucket": "test-bucket",
            "cos_host": "https://cos.example.com",
        }
    )
    service = TestingScreenshotService(settings)

    cover_url = service.generate_screenshot("http://localhost/demo/")

    assert cover_url is not None
    assert cover_url.startswith("https://cos.example.com/screenshots/")
    assert cover_url.endswith(".png")
    assert list(Path(settings.screenshot_root).rglob("*")) == []


def test_cos_uploader_builds_java_aligned_key(tmp_path: Path) -> None:
    settings = build_settings(
        {
            "repo_root": str(tmp_path),
            "cos_secret_id": "test-secret-id",
            "cos_secret_key": "test-secret-key",
            "cos_region": "ap-shanghai",
            "cos_bucket": "test-bucket",
            "cos_host": "https://cos.example.com",
        }
    )
    uploader = CosScreenshotUploader(settings)

    key = uploader.build_object_key("cover.png")

    assert key.startswith("/screenshots/")
    assert key.endswith("/cover.png")


def test_cos_uploader_supports_v5_sdk_shape(tmp_path: Path) -> None:
    settings = build_settings(
        {
            "repo_root": str(tmp_path),
            "cos_secret_id": "test-secret-id",
            "cos_secret_key": "test-secret-key",
            "cos_region": "ap-shanghai",
            "cos_bucket": "bucket-1234567890",
            "cos_host": "https://cos.example.com",
        }
    )
    uploader = CosScreenshotUploader(settings)
    capture: dict[str, object] = {}

    class FakeCosConfig:
        def __init__(self, Region: str, SecretId: str, SecretKey: str):
            capture["region"] = Region
            capture["secret_id"] = SecretId
            capture["secret_key"] = SecretKey

    class FakeCosS3Client:
        def __init__(self, config):
            capture["config"] = config

        def put_object(self, **kwargs):
            capture["kwargs"] = kwargs
            return {"ETag": "demo"}

    screenshot_file = tmp_path / "cover.png"
    screenshot_file.write_bytes(b"png")

    uploader._upload_with_sdk(
        SimpleNamespace(CosConfig=FakeCosConfig, CosS3Client=FakeCosS3Client),
        screenshot_file,
        "/screenshots/2026/04/07/cover.png",
    )

    assert capture["region"] == "ap-shanghai"
    assert capture["secret_id"] == "test-secret-id"
    assert capture["secret_key"] == "test-secret-key"
    assert capture["kwargs"]["Bucket"] == "bucket-1234567890"
    assert capture["kwargs"]["Key"] == "/screenshots/2026/04/07/cover.png"


def test_cos_uploader_rejects_legacy_sdk_shape(tmp_path: Path) -> None:
    settings = build_settings(
        {
            "repo_root": str(tmp_path),
            "cos_secret_id": "test-secret-id",
            "cos_secret_key": "test-secret-key",
            "cos_region": "ap-shanghai",
            "cos_bucket": "bucket-1234567890",
            "cos_host": "https://cos.example.com",
        }
    )
    uploader = CosScreenshotUploader(settings)
    screenshot_file = tmp_path / "cover.png"
    screenshot_file.write_bytes(b"png")

    try:
        uploader._upload_with_sdk(SimpleNamespace(CosConfig=object), screenshot_file, "/screenshots/demo.png")
    except RuntimeError as exc:
        assert "cos-python-sdk-v5" in str(exc)
    else:
        raise AssertionError("预期旧版 SDK 被拒绝")
