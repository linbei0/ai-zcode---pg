from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    app = create_app(
        {
            "database_url": f"sqlite:///{tmp_path / 'test.db'}",
            "redis_url": "redis://unused",
            "session_secret": "test-secret",
            "repo_root": str(tmp_path),
            "testing": True,
        }
    )
    return TestClient(app)


def register_and_login(client: TestClient, user_account: str = "vueBuilder") -> None:
    register_res = client.post(
        "/api/user/register",
        json={
            "userAccount": user_account,
            "userPassword": "password123",
            "checkPassword": "password123",
        },
    )
    assert register_res.status_code == 200
    assert register_res.json()["code"] == 0

    login_res = client.post(
        "/api/user/login",
        json={"userAccount": user_account, "userPassword": "password123"},
    )
    assert login_res.status_code == 200
    assert login_res.json()["code"] == 0


def test_vue_generation_builds_preview_dist(tmp_path: Path, monkeypatch) -> None:
    client = build_client(tmp_path)
    register_and_login(client)

    add_res = client.post("/api/app/add", json={"initPrompt": "生成一个 Vue 商城网站"})
    assert add_res.status_code == 200
    app_id = add_res.json()["data"]

    def fake_run_command(self, command: str, cwd: Path) -> None:
        dist_dir = cwd / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        (dist_dir / "index.html").write_text("<html><body>preview ready</body></html>", encoding="utf-8")

    monkeypatch.setattr("app.services.storage_service.StorageService._run_command", fake_run_command)

    with client.stream(
        "GET",
        "/api/app/chat/gen/code",
        params={"appId": app_id, "message": "做一个带商品列表和购物车的 Vue 商城"},
    ) as response:
        assert response.status_code == 200
        raw_stream = "\n".join(line for line in response.iter_lines() if line)

    assert "event: done" in raw_stream

    preview_res = client.get(f"/api/static/vue_project_{app_id}/dist/index.html")
    assert preview_res.status_code == 200
    assert "preview ready" in preview_res.text
