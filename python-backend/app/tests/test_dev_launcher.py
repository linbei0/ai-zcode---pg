from pathlib import Path

from app.dev_launcher import LauncherPaths, build_runtime_env, parse_listening_pid, render_nginx_config


def test_build_runtime_env_sets_default_code_deploy_host() -> None:
    env = build_runtime_env({}, nginx_port=80)
    assert env["AIZCODE_CODE_DEPLOY_HOST"] == "http://localhost"

    env = build_runtime_env({}, nginx_port=8088)
    assert env["AIZCODE_CODE_DEPLOY_HOST"] == "http://localhost:8088"


def test_build_runtime_env_keeps_explicit_code_deploy_host() -> None:
    env = build_runtime_env({"AIZCODE_CODE_DEPLOY_HOST": "https://example.com"}, nginx_port=80)
    assert env["AIZCODE_CODE_DEPLOY_HOST"] == "https://example.com"


def test_parse_listening_pid_from_windows_netstat_output() -> None:
    sample = """
  TCP    127.0.0.1:80           0.0.0.0:0              LISTENING       4321
  TCP    127.0.0.1:8335         0.0.0.0:0              LISTENING       9876
"""
    assert parse_listening_pid(sample, 80) == 4321
    assert parse_listening_pid(sample, 8335) == 9876
    assert parse_listening_pid(sample, 5173) is None


def test_render_nginx_config_targets_code_deploy_root_and_spa_fallback(tmp_path: Path) -> None:
    paths = LauncherPaths.from_repo_root(tmp_path)
    config_text = render_nginx_config(paths, nginx_port=80)

    assert str(paths.code_deploy_root).replace("\\", "/") in config_text.replace("\\", "/")
    assert "location = / {" in config_text
    assert "try_files $uri $uri/ @deploy_spa;" in config_text
    assert "rewrite ^/([^/]+)/.*$ /$1/index.html break;" in config_text
    assert str(paths.pid_file).replace("\\", "/") in config_text.replace("\\", "/")
