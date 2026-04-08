import sqlite3
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import build_settings
from app.services.ai_service import TestingAIGateway
from app.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    app = create_app(
        {
            "database_url": f"sqlite:///{tmp_path / 'test.db'}",
            "redis_url": "redis://unused",
            "session_secret": "test-secret",
            "repo_root": str(tmp_path),
            "testing": True,
            "cos_secret_id": "test-secret-id",
            "cos_secret_key": "test-secret-key",
            "cos_region": "ap-shanghai",
            "cos_bucket": "test-bucket",
            "cos_host": "https://cos.example.com",
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


def test_cors_allows_frontend_origin_with_credentials(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get(
        "/api/health/",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_blank_openai_base_url_is_normalized_to_none() -> None:
    settings = build_settings({"openai_api_key": "demo-key", "openai_base_url": "   "})
    assert settings.openai_base_url is None


def test_testing_ai_gateway_routes_code_type() -> None:
    gateway = TestingAIGateway()
    assert gateway.route_code_type("生成一个极简 HTML 页面") == "html"
    assert gateway.route_code_type("生成一个带交互的 JS 页面") == "multi_file"
    assert gateway.route_code_type("生成一个 Vue 后台系统") == "vue_project"


def test_testing_ai_gateway_optimizes_prompt() -> None:
    gateway = TestingAIGateway()

    create_result = gateway.optimize_prompt("做一个博客", "create_app")
    assert create_result["mode"] == "basic"
    assert "产品类型" in create_result["optimizedPrompt"]
    assert "做一个博客" in create_result["optimizedPrompt"]

    chat_result = gateway.optimize_prompt(
        "把首页按钮改成蓝色",
        "chat",
        {"appName": "博客站点", "initPrompt": "创建一个博客", "codeGenType": "vue_project"},
    )
    assert chat_result["mode"] == "detail"
    assert "当前应用" in chat_result["optimizedPrompt"]
    assert "把首页按钮改成蓝色" in chat_result["optimizedPrompt"]


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


def test_prompt_optimize_endpoint_returns_optimized_prompt_without_history_mutation(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    register_and_login(client, user_account="optimizer")

    add_res = client.post("/api/app/add", json={"initPrompt": "生成一个极简 HTML 页面"})
    app_id = add_res.json()["data"]

    optimize_res = client.post(
        "/api/app/prompt/optimize",
        json={"prompt": "做一个个人博客网站", "scene": "create_app"},
    )
    assert optimize_res.status_code == 200
    assert optimize_res.json()["code"] == 0
    optimize_data = optimize_res.json()["data"]
    assert optimize_data["mode"] == "basic"
    assert "做一个个人博客网站" in optimize_data["optimizedPrompt"]

    chat_optimize_res = client.post(
        "/api/app/prompt/optimize",
        json={"prompt": "把首页按钮改成蓝色并更现代", "scene": "chat", "appId": app_id},
    )
    assert chat_optimize_res.status_code == 200
    assert chat_optimize_res.json()["code"] == 0
    chat_optimize_data = chat_optimize_res.json()["data"]
    assert chat_optimize_data["mode"] == "detail"
    assert "当前应用" in chat_optimize_data["optimizedPrompt"]

    history_res = client.get(f"/api/chatHistory/app/{app_id}", params={"pageSize": 10})
    assert history_res.status_code == 200
    assert history_res.json()["code"] == 0
    assert history_res.json()["data"]["records"] == []

    app_res = client.get("/api/app/get/vo", params={"id": app_id})
    assert app_res.status_code == 200
    assert app_res.json()["code"] == 0
    assert app_res.json()["data"]["initPrompt"] == "生成一个极简 HTML 页面"


def test_prompt_optimize_requires_login(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    res = client.post(
        "/api/app/prompt/optimize",
        json={"prompt": "做一个个人博客网站", "scene": "create_app"},
    )

    assert res.status_code == 200
    assert res.json()["code"] == 40100


def test_prompt_optimize_rejects_blank_prompt(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    register_and_login(client, user_account="blankPromptUser")

    res = client.post(
        "/api/app/prompt/optimize",
        json={"prompt": "   ", "scene": "create_app"},
    )

    assert res.status_code == 200
    assert res.json()["code"] == 40000


def test_prompt_optimize_chat_scope_requires_owner(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    register_and_login(client, user_account="ownerA")
    add_res = client.post("/api/app/add", json={"initPrompt": "生成一个极简 HTML 页面"})
    app_id = add_res.json()["data"]
    client.post("/api/user/logout")
    register_and_login(client, user_account="ownerB")

    res = client.post(
        "/api/app/prompt/optimize",
        json={"prompt": "改一下首页布局", "scene": "chat", "appId": app_id},
    )

    assert res.status_code == 200
    assert res.json()["code"] == 40101


def test_workflow_execute_and_stream_endpoints(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    execute_res = client.post("/api/workflow/execute", params={"prompt": "生成一个极简 HTML 页面"})
    assert execute_res.status_code == 200
    assert execute_res.json()["originalPrompt"] == "生成一个极简 HTML 页面"
    assert execute_res.json()["generationType"] in {"html", "multi_file", "vue_project"}
    assert execute_res.json()["qualityResult"]["isValid"] is True

    flux_res = client.get("/api/workflow/execute-flux", params={"prompt": "生成一个极简 HTML 页面"})
    assert flux_res.status_code == 200
    assert "event: workflow_start" in flux_res.text
    assert "event: workflow_completed" in flux_res.text

    sse_res = client.get("/api/workflow/execute-sse", params={"prompt": "生成一个极简 HTML 页面"})
    assert sse_res.status_code == 200
    assert "event: workflow_start" in sse_res.text
    assert "event: workflow_completed" in sse_res.text


def test_chat_endpoint_rate_limit_returns_business_error_event(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    register_and_login(client, user_account="limited")

    add_res = client.post("/api/app/add", json={"initPrompt": "生成一个极简 HTML 页面"})
    app_id = add_res.json()["data"]

    for _ in range(5):
        ok_res = client.get(
            "/api/app/chat/gen/code",
            params={"appId": app_id, "message": "短一点的生成请求"},
        )
        assert ok_res.status_code == 200
        assert "event: done" in ok_res.text

    limited_res = client.get(
        "/api/app/chat/gen/code",
        params={"appId": app_id, "message": "第六次请求应该被限流"},
    )
    assert limited_res.status_code == 200
    assert "event: business-error" in limited_res.text
    assert '"code":42900' in limited_res.text or '"code":42900'.replace(" ", "") in limited_res.text


def test_prompt_optimize_endpoint_rate_limit_returns_business_error(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    client.app.state.settings.prompt_optimize_rate_limit = 2
    client.app.state.settings.prompt_optimize_rate_interval_seconds = 60
    register_and_login(client, user_account="optLimited")

    for _ in range(2):
        ok_res = client.post(
            "/api/app/prompt/optimize",
            json={"prompt": "做一个营销落地页", "scene": "create_app"},
        )
        assert ok_res.status_code == 200
        assert ok_res.json()["code"] == 0

    limited_res = client.post(
        "/api/app/prompt/optimize",
        json={"prompt": "第三次优化应该被限流", "scene": "create_app"},
    )
    assert limited_res.status_code == 200
    assert limited_res.json()["code"] == 42900


def test_deploy_updates_cover_after_screenshot(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    register_and_login(client, user_account="coverUser")

    add_res = client.post("/api/app/add", json={"initPrompt": "生成一个极简 HTML 页面"})
    app_id = add_res.json()["data"]

    client.get(
        "/api/app/chat/gen/code",
        params={"appId": app_id, "message": "给我一个带标题和按钮的页面"},
    )
    deploy_res = client.post("/api/app/deploy", json={"appId": app_id})
    assert deploy_res.status_code == 200
    assert deploy_res.json()["code"] == 0

    deadline = time.time() + 3
    cover = None
    while time.time() < deadline:
        app_res = client.get("/api/app/get/vo", params={"id": app_id})
        cover = app_res.json()["data"].get("cover")
        if cover:
            break
        time.sleep(0.1)

    assert cover
    assert cover.startswith("https://cos.example.com/screenshots/")
    assert cover.endswith(".png")


def test_deploy_keeps_success_when_screenshot_pipeline_fails(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    register_and_login(client, user_account="coverFailureUser")
    client.app.state.screenshot_service.should_fail = True

    add_res = client.post("/api/app/add", json={"initPrompt": "生成一个极简 HTML 页面"})
    app_id = add_res.json()["data"]

    client.get(
        "/api/app/chat/gen/code",
        params={"appId": app_id, "message": "给我一个带标题和按钮的页面"},
    )
    deploy_res = client.post("/api/app/deploy", json={"appId": app_id})
    assert deploy_res.status_code == 200
    assert deploy_res.json()["code"] == 0

    time.sleep(0.2)
    app_res = client.get("/api/app/get/vo", params={"id": app_id})
    assert app_res.status_code == 200
    assert app_res.json()["data"].get("cover") is None


def test_deploy_does_not_clear_existing_cover_when_screenshot_pipeline_fails(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    register_and_login(client, user_account="coverRetainUser")

    add_res = client.post("/api/app/add", json={"initPrompt": "生成一个极简 HTML 页面"})
    app_id = add_res.json()["data"]

    client.get(
        "/api/app/chat/gen/code",
        params={"appId": app_id, "message": "给我一个带标题和按钮的页面"},
    )
    first_deploy_res = client.post("/api/app/deploy", json={"appId": app_id})
    assert first_deploy_res.status_code == 200
    assert first_deploy_res.json()["code"] == 0

    deadline = time.time() + 3
    cover = None
    while time.time() < deadline:
        app_res = client.get("/api/app/get/vo", params={"id": app_id})
        cover = app_res.json()["data"].get("cover")
        if cover:
            break
        time.sleep(0.1)

    assert cover

    client.app.state.screenshot_service.should_fail = True
    second_deploy_res = client.post("/api/app/deploy", json={"appId": app_id})
    assert second_deploy_res.status_code == 200
    assert second_deploy_res.json()["code"] == 0

    time.sleep(0.2)
    latest_app_res = client.get("/api/app/get/vo", params={"id": app_id})
    assert latest_app_res.status_code == 200
    assert latest_app_res.json()["data"].get("cover") == cover


def test_good_app_list_uses_cache_and_invalidates_on_admin_update(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    register_and_login(client, user_account="cacheUser")

    add_res = client.post("/api/app/add", json={"initPrompt": "生成一个缓存测试页面"})
    app_id = add_res.json()["data"]

    client.post("/api/workflow/testing/promote-admin")
    client.post(
        "/api/app/admin/update",
        json={"id": app_id, "appName": "缓存前名称", "priority": 99},
    )

    first_res = client.post("/api/app/good/list/page/vo", json={"pageNum": 1, "pageSize": 10})
    assert first_res.status_code == 200
    assert first_res.json()["data"]["records"][0]["appName"] == "缓存前名称"

    sqlite_conn = sqlite3.connect(tmp_path / "test.db")
    sqlite_conn.execute("update app set app_name = ? where id = ?", ("数据库直改名称", app_id))
    sqlite_conn.commit()
    sqlite_conn.close()

    cached_res = client.post("/api/app/good/list/page/vo", json={"pageNum": 1, "pageSize": 10})
    assert cached_res.status_code == 200
    assert cached_res.json()["data"]["records"][0]["appName"] == "缓存前名称"

    client.post(
        "/api/app/admin/update",
        json={"id": app_id, "appName": "缓存失效后名称", "priority": 99},
    )
    invalidated_res = client.post("/api/app/good/list/page/vo", json={"pageNum": 1, "pageSize": 10})
    assert invalidated_res.status_code == 200
    assert invalidated_res.json()["data"]["records"][0]["appName"] == "缓存失效后名称"


def test_toggle_featured_by_admin_keeps_existing_name_and_cover(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    register_and_login(client, user_account="featuredUser")

    add_res = client.post("/api/app/add", json={"initPrompt": "创建一个现代化的企业官网"})
    app_id = add_res.json()["data"]

    client.post("/api/workflow/testing/promote-admin")
    client.post(
        "/api/app/admin/update",
        json={
            "id": app_id,
            "appName": "企业官网",
            "cover": "https://example.com/cover.png",
            "priority": 0,
        },
    )

    toggle_res = client.post(
        "/api/app/admin/update",
        json={
            "id": app_id,
            "priority": 99,
        },
    )
    assert toggle_res.status_code == 200
    assert toggle_res.json()["code"] == 0

    app_res = client.get("/api/app/get/vo", params={"id": app_id})
    assert app_res.status_code == 200
    assert app_res.json()["data"]["appName"] == "企业官网"
    assert app_res.json()["data"]["cover"] == "https://example.com/cover.png"
    assert app_res.json()["data"]["priority"] == 99
