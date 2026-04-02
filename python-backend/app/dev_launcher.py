from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_NGINX_PORT = 80
DEFAULT_PYTHON_HOST = "127.0.0.1"
DEFAULT_PYTHON_PORT = 8335
DEFAULT_NGINX_DOWNLOAD_URL = "https://nginx.org/download/nginx-1.28.0.zip"
POLL_INTERVAL_SECONDS = 0.2
POLL_TIMEOUT_SECONDS = 8


@dataclass(frozen=True)
class LauncherPaths:
    repo_root: Path
    backend_root: Path
    runtime_root: Path
    nginx_root: Path
    nginx_dist_root: Path
    nginx_conf_dir: Path
    nginx_logs_dir: Path
    nginx_temp_dir: Path
    code_deploy_root: Path
    nginx_binary: Path
    mime_types_file: Path
    config_file: Path
    pid_file: Path

    @classmethod
    def from_repo_root(cls, repo_root: Path) -> "LauncherPaths":
        resolved_repo_root = repo_root.resolve()
        backend_root = resolved_repo_root / "python-backend"
        runtime_root = resolved_repo_root / ".runtime"
        nginx_root = runtime_root / "nginx"
        nginx_dist_root = nginx_root / "dist"
        nginx_conf_dir = nginx_root / "conf"
        nginx_logs_dir = nginx_root / "logs"
        nginx_temp_dir = nginx_root / "temp"
        return cls(
            repo_root=resolved_repo_root,
            backend_root=backend_root,
            runtime_root=runtime_root,
            nginx_root=nginx_root,
            nginx_dist_root=nginx_dist_root,
            nginx_conf_dir=nginx_conf_dir,
            nginx_logs_dir=nginx_logs_dir,
            nginx_temp_dir=nginx_temp_dir,
            code_deploy_root=resolved_repo_root / "tmp" / "code_deploy",
            nginx_binary=nginx_dist_root / "nginx.exe",
            mime_types_file=nginx_dist_root / "conf" / "mime.types",
            config_file=nginx_conf_dir / "nginx.dev.conf",
            pid_file=nginx_root / "nginx.pid",
        )


class LauncherError(RuntimeError):
    pass


def log_status(message: str) -> None:
    print(f"[aizcode-dev] {message}", flush=True)


def build_runtime_env(base_env: dict[str, str], nginx_port: int) -> dict[str, str]:
    runtime_env = dict(base_env)
    if not runtime_env.get("AIZCODE_CODE_DEPLOY_HOST"):
        runtime_env["AIZCODE_CODE_DEPLOY_HOST"] = build_deploy_host(nginx_port)
    return runtime_env


def build_deploy_host(nginx_port: int) -> str:
    if nginx_port == 80:
        return "http://localhost"
    return f"http://localhost:{nginx_port}"


def parse_listening_pid(netstat_output: str, port: int) -> int | None:
    for line in netstat_output.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        local_address = parts[1]
        state = parts[3]
        pid_text = parts[4]
        if state.upper() != "LISTENING":
            continue
        if not local_address.endswith(f":{port}"):
            continue
        try:
            return int(pid_text)
        except ValueError:
            continue
    return None


def render_nginx_config(paths: LauncherPaths, nginx_port: int) -> str:
    code_deploy_root = normalize_nginx_path(paths.code_deploy_root)
    mime_types_path = normalize_nginx_path(paths.mime_types_file)
    pid_path = normalize_nginx_path(paths.pid_file)
    error_log_path = normalize_nginx_path(paths.nginx_logs_dir / "error.log")
    access_log_path = normalize_nginx_path(paths.nginx_logs_dir / "access.log")
    client_temp_path = normalize_nginx_path(paths.nginx_temp_dir / "client_body")
    proxy_temp_path = normalize_nginx_path(paths.nginx_temp_dir / "proxy")
    fastcgi_temp_path = normalize_nginx_path(paths.nginx_temp_dir / "fastcgi")
    uwsgi_temp_path = normalize_nginx_path(paths.nginx_temp_dir / "uwsgi")
    scgi_temp_path = normalize_nginx_path(paths.nginx_temp_dir / "scgi")
    return f"""
worker_processes  1;

pid "{pid_path}";
error_log "{error_log_path}";

events {{
    worker_connections 1024;
}}

http {{
    include "{mime_types_path}";
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    access_log "{access_log_path}";
    client_body_temp_path "{client_temp_path}";
    proxy_temp_path "{proxy_temp_path}";
    fastcgi_temp_path "{fastcgi_temp_path}";
    uwsgi_temp_path "{uwsgi_temp_path}";
    scgi_temp_path "{scgi_temp_path}";

    server {{
        listen 127.0.0.1:{nginx_port};
        server_name localhost;
        root "{code_deploy_root}";
        autoindex off;

        location = / {{
            return 404;
        }}

        location / {{
            try_files $uri $uri/ @deploy_spa;
        }}

        location @deploy_spa {{
            rewrite ^/([^/]+)/.*$ /$1/index.html break;
            try_files $uri =404;
        }}
    }}
}}
""".strip()


def normalize_nginx_path(path: Path) -> str:
    return path.resolve().as_posix()


def is_truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_launcher_paths() -> LauncherPaths:
    return LauncherPaths.from_repo_root(resolve_repo_root())


def resolve_nginx_port() -> int:
    raw_value = os.environ.get("AIZCODE_NGINX_PORT", str(DEFAULT_NGINX_PORT)).strip()
    try:
        port = int(raw_value)
    except ValueError as exc:
        raise LauncherError(f"AIZCODE_NGINX_PORT 无效：{raw_value}") from exc
    if port <= 0 or port > 65535:
        raise LauncherError(f"AIZCODE_NGINX_PORT 超出范围：{port}")
    return port


def resolve_download_url() -> str:
    return os.environ.get("AIZCODE_NGINX_DOWNLOAD_URL", DEFAULT_NGINX_DOWNLOAD_URL).strip()


def ensure_runtime_dirs(paths: LauncherPaths) -> None:
    for directory in (
        paths.runtime_root,
        paths.nginx_root,
        paths.nginx_dist_root,
        paths.nginx_conf_dir,
        paths.nginx_logs_dir,
        paths.nginx_temp_dir,
        paths.code_deploy_root,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def ensure_nginx_binary(paths: LauncherPaths, download_url: str) -> Path:
    if paths.nginx_binary.exists() and paths.mime_types_file.exists():
        log_status(f"复用本地 Nginx：{paths.nginx_binary}")
        return paths.nginx_binary

    ensure_runtime_dirs(paths)
    archive_name = Path(download_url).name or "nginx.zip"
    archive_path = paths.nginx_root / archive_name
    extract_root = paths.nginx_root / "_extract"

    if extract_root.exists():
        shutil.rmtree(extract_root)
    if archive_path.exists():
        archive_path.unlink()

    try:
        log_status(f"开始下载 Nginx：{download_url}")
        with urllib.request.urlopen(download_url) as response, archive_path.open("wb") as target_file:
            shutil.copyfileobj(response, target_file)
        with zipfile.ZipFile(archive_path) as zip_file:
            zip_file.extractall(extract_root)
    except Exception as exc:
        raise LauncherError(
            f"Nginx 下载或解压失败，URL={download_url}，目标目录={paths.nginx_dist_root}"
        ) from exc

    extracted_binary = next(extract_root.rglob("nginx.exe"), None)
    if extracted_binary is None:
        raise LauncherError(f"下载内容中未找到 nginx.exe，URL={download_url}")

    extracted_root = extracted_binary.parent
    if paths.nginx_dist_root.exists():
        shutil.rmtree(paths.nginx_dist_root)
    shutil.copytree(extracted_root, paths.nginx_dist_root)

    if not paths.mime_types_file.exists():
        raise LauncherError(f"Nginx 缺少 mime.types：{paths.mime_types_file}")
    log_status(f"Nginx 已安装到：{paths.nginx_dist_root}")
    return paths.nginx_binary


def write_nginx_config(paths: LauncherPaths, nginx_port: int) -> None:
    ensure_runtime_dirs(paths)
    paths.config_file.write_text(render_nginx_config(paths, nginx_port), encoding="utf-8")


def get_listening_pid(port: int) -> int | None:
    result = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    return parse_listening_pid(result.stdout, port)


def read_managed_pid(paths: LauncherPaths) -> int | None:
    if not paths.pid_file.exists():
        return None
    try:
        return int(paths.pid_file.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def process_exists(pid: int) -> bool:
    result = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    output = result.stdout.strip()
    if not output:
        return False
    return "INFO:" not in output.upper()


def remove_stale_pid_file(paths: LauncherPaths) -> None:
    managed_pid = read_managed_pid(paths)
    if managed_pid is not None and not process_exists(managed_pid):
        paths.pid_file.unlink(missing_ok=True)


def run_nginx(paths: LauncherPaths, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(paths.nginx_binary),
            "-p",
            f"{normalize_nginx_path(paths.nginx_dist_root)}/",
            "-c",
            normalize_nginx_path(paths.config_file),
            *args,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
        cwd=paths.nginx_dist_root,
    )


def ensure_valid_nginx_config(paths: LauncherPaths) -> None:
    log_status(f"校验 Nginx 配置：{paths.config_file}")
    result = run_nginx(paths, "-t")
    if result.returncode != 0:
        raise LauncherError(f"Nginx 配置校验失败：\n{result.stdout}\n{result.stderr}".strip())


def wait_for_port(port: int, timeout_seconds: float = POLL_TIMEOUT_SECONDS) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if get_listening_pid(port) is not None:
            return
        time.sleep(POLL_INTERVAL_SECONDS)
    raise LauncherError(f"Nginx 启动超时，端口 {port} 未进入监听状态")


def ensure_nginx_running(paths: LauncherPaths, nginx_port: int, download_url: str) -> bool:
    ensure_nginx_binary(paths, download_url)
    write_nginx_config(paths, nginx_port)
    remove_stale_pid_file(paths)
    ensure_valid_nginx_config(paths)

    port_pid = get_listening_pid(nginx_port)
    managed_pid = read_managed_pid(paths)
    managed_alive = managed_pid is not None and process_exists(managed_pid)

    if port_pid is not None:
        if managed_alive:
            log_status(f"检测到受管 Nginx 已在端口 {nginx_port} 运行，执行配置重载")
            reload_result = run_nginx(paths, "-s", "reload")
            if reload_result.returncode != 0:
                raise LauncherError(
                    f"受管 Nginx 重载失败：\n{reload_result.stdout}\n{reload_result.stderr}".strip()
                )
            wait_for_port(nginx_port)
            return False
        raise LauncherError(f"Nginx 端口 {nginx_port} 已被非受管进程占用，PID={port_pid}")

    log_status(f"启动 Nginx，监听 http://localhost{'' if nginx_port == 80 else f':{nginx_port}'}/")
    start_result = run_nginx(paths)
    if start_result.returncode != 0:
        raise LauncherError(f"Nginx 启动失败：\n{start_result.stdout}\n{start_result.stderr}".strip())
    wait_for_port(nginx_port)
    return True


def stop_managed_nginx(paths: LauncherPaths) -> None:
    managed_pid = read_managed_pid(paths)
    if managed_pid is None or not process_exists(managed_pid):
        return
    log_status("关闭受管 Nginx")
    stop_result = run_nginx(paths, "-s", "quit")
    if stop_result.returncode != 0:
        raise LauncherError(f"Nginx 关闭失败：\n{stop_result.stdout}\n{stop_result.stderr}".strip())


def start_uvicorn(env: dict[str, str]) -> int:
    log_status(f"启动 Python API：http://{DEFAULT_PYTHON_HOST}:{DEFAULT_PYTHON_PORT}/api")
    log_status("前台服务已启动，保持此窗口打开，按 Ctrl+C 可退出")
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        DEFAULT_PYTHON_HOST,
        "--port",
        str(DEFAULT_PYTHON_PORT),
        "--reload",
    ]
    process = subprocess.Popen(command, cwd=resolve_launcher_paths().backend_root, env=env)
    try:
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        return process.wait()


def main() -> int:
    paths = resolve_launcher_paths()
    os.chdir(paths.backend_root)
    nginx_port = resolve_nginx_port()
    runtime_env = build_runtime_env(os.environ.copy(), nginx_port)
    auto_start_nginx = is_truthy(runtime_env.get("AIZCODE_NGINX_AUTO_START"), default=True)
    started_managed_nginx = False

    try:
        if auto_start_nginx:
            started_managed_nginx = ensure_nginx_running(paths, nginx_port, resolve_download_url())
        else:
            log_status("已跳过 Nginx 自动启动（AIZCODE_NGINX_AUTO_START=false）")
        return start_uvicorn(runtime_env)
    except LauncherError as exc:
        print(f"[aizcode-dev] {exc}", file=sys.stderr)
        return 1
    finally:
        if started_managed_nginx:
            try:
                stop_managed_nginx(paths)
            except LauncherError as exc:
                print(f"[aizcode-dev] {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
