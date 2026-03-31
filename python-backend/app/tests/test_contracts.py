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


def register_and_login(client: TestClient, user_account: str = "demoUser") -> None:
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


def test_user_register_login_logout_and_get_login_user(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    register_and_login(client)

    login_user_res = client.get("/api/user/get/login")
    assert login_user_res.status_code == 200
    assert login_user_res.json()["code"] == 0
    assert login_user_res.json()["data"]["userAccount"] == "demoUser"

    logout_res = client.post("/api/user/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["code"] == 0

    not_login_res = client.get("/api/user/get/login")
    assert not_login_res.status_code == 200
    assert not_login_res.json()["code"] == 40100


def test_app_crud_pagination_and_admin_views(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    register_and_login(client)

    add_res = client.post("/api/app/add", json={"initPrompt": "生成一个简洁的作品集主页"})
    assert add_res.status_code == 200
    assert add_res.json()["code"] == 0
    app_id = add_res.json()["data"]

    get_res = client.get("/api/app/get/vo", params={"id": app_id})
    assert get_res.status_code == 200
    assert get_res.json()["code"] == 0
    assert get_res.json()["data"]["id"] == app_id
    assert get_res.json()["data"]["codeGenType"] in {"html", "multi_file", "vue_project"}

    my_list_res = client.post(
        "/api/app/my/list/page/vo",
        json={"pageNum": 1, "pageSize": 10, "sortField": "create_time", "sortOrder": "desc"},
    )
    assert my_list_res.status_code == 200
    assert my_list_res.json()["code"] == 0
    assert my_list_res.json()["data"]["totalRow"] == 1

    update_res = client.post("/api/app/update", json={"id": app_id, "appName": "我的新名字"})
    assert update_res.status_code == 200
    assert update_res.json()["code"] == 0

    admin_bootstrap_res = client.post("/api/workflow/testing/promote-admin")
    assert admin_bootstrap_res.status_code == 200
    assert admin_bootstrap_res.json()["code"] == 0

    user_page_res = client.post("/api/user/list/page/vo", json={"pageNum": 1, "pageSize": 10})
    assert user_page_res.status_code == 200
    assert user_page_res.json()["code"] == 0

    app_page_res = client.post("/api/app/admin/list/page/vo", json={"pageNum": 1, "pageSize": 10})
    assert app_page_res.status_code == 200
    assert app_page_res.json()["code"] == 0
    assert app_page_res.json()["data"]["records"][0]["id"] == app_id

    chat_page_res = client.post(
        "/api/chatHistory/admin/list/page/vo",
        json={"pageNum": 1, "pageSize": 10},
    )
    assert chat_page_res.status_code == 200
    assert chat_page_res.json()["code"] == 0


def test_chat_generation_sse_persists_history_and_supports_preview_deploy_download(
    tmp_path: Path,
) -> None:
    client = build_client(tmp_path)
    register_and_login(client, user_account="builder")

    add_res = client.post("/api/app/add", json={"initPrompt": "生成一个极简 HTML 页面"})
    app_id = add_res.json()["data"]

    with client.stream(
        "GET",
        "/api/app/chat/gen/code",
        params={"appId": app_id, "message": "给我一个带标题和按钮的页面"},
    ) as response:
        assert response.status_code == 200
        raw_stream = "\n".join(line for line in response.iter_lines() if line)

    assert 'data: {"d":"' in raw_stream
    assert "event: done" in raw_stream

    history_res = client.get(f"/api/chatHistory/app/{app_id}", params={"pageSize": 10})
    assert history_res.status_code == 200
    assert history_res.json()["code"] == 0
    assert len(history_res.json()["data"]["records"]) == 2

    preview_res = client.get(f"/api/static/html_{app_id}/")
    assert preview_res.status_code == 200
    assert "text/html" in preview_res.headers["content-type"]
    assert "<html" in preview_res.text.lower()

    deploy_res = client.post("/api/app/deploy", json={"appId": app_id})
    assert deploy_res.status_code == 200
    assert deploy_res.json()["code"] == 0
    assert deploy_res.json()["data"].endswith("/")

    download_res = client.get(f"/api/app/download/{app_id}")
    assert download_res.status_code == 200
    assert "application/zip" in download_res.headers["content-type"]
