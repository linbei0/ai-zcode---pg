from __future__ import annotations

import shutil
import subprocess
import zipfile
from io import BytesIO
from pathlib import Path

from app.ai.parsers import extract_html, extract_multi_file, extract_vue_project_files
from app.core.config import Settings
from app.core.exceptions import BusinessException, ErrorCode


class StorageService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.code_output_root.mkdir(parents=True, exist_ok=True)
        self.settings.code_deploy_root.mkdir(parents=True, exist_ok=True)

    def output_dir(self, code_gen_type: str, identifier: int | str) -> Path:
        return self.settings.code_output_root / f"{code_gen_type}_{identifier}"

    def save_generated_code(self, code_gen_type: str, identifier: int | str, content: str) -> Path:
        target_dir = self.output_dir(code_gen_type, identifier)
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        if code_gen_type == "html":
            (target_dir / "index.html").write_text(extract_html(content), encoding="utf-8")
        elif code_gen_type == "multi_file":
            for file_name, file_content in extract_multi_file(content).items():
                (target_dir / file_name).write_text(file_content, encoding="utf-8")
        elif code_gen_type == "vue_project":
            for relative_path, file_content in extract_vue_project_files(content).items():
                file_path = target_dir / relative_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file_content, encoding="utf-8")
        else:
            raise BusinessException(ErrorCode.SYSTEM_ERROR, "不支持的代码生成类型")
        return target_dir

    def deploy(self, code_gen_type: str, app_id: int, deploy_key: str) -> str:
        source_dir = self.output_dir(code_gen_type, app_id)
        if not source_dir.exists():
            raise BusinessException(ErrorCode.SYSTEM_ERROR, "应用代码不存在，请先生成代码")

        deploy_source = source_dir
        if code_gen_type == "vue_project":
            self._run_command(self.settings.vue_install_command, source_dir)
            self._run_command(self.settings.vue_build_command, source_dir)
            dist_dir = source_dir / "dist"
            if not dist_dir.exists():
                raise BusinessException(ErrorCode.SYSTEM_ERROR, "Vue 项目构建完成但未生成 dist 目录")
            deploy_source = dist_dir

        deploy_dir = self.settings.code_deploy_root / deploy_key
        if deploy_dir.exists():
            shutil.rmtree(deploy_dir)
        shutil.copytree(deploy_source, deploy_dir)
        return f"{self.settings.code_deploy_host}/{deploy_key}/"

    def build_vue_project_if_needed(self, code_gen_type: str, source_dir: Path) -> Path | None:
        if code_gen_type != "vue_project":
            return None
        self._run_command(self.settings.vue_install_command, source_dir)
        self._run_command(self.settings.vue_build_command, source_dir)
        dist_dir = source_dir / "dist"
        if not dist_dir.exists():
            raise BusinessException(ErrorCode.SYSTEM_ERROR, "Vue 项目构建完成但未生成 dist 目录")
        return dist_dir

    def build_download_zip(self, code_gen_type: str, app_id: int) -> bytes:
        source_dir = self.output_dir(code_gen_type, app_id)
        if not source_dir.exists():
            raise BusinessException(ErrorCode.NOT_FOUND_ERROR, "应用代码不存在，请先生成代码")
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    zip_file.write(file_path, arcname=file_path.relative_to(source_dir))
        return buffer.getvalue()

    def _run_command(self, command: str, cwd: Path) -> None:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode != 0:
            raise BusinessException(
                ErrorCode.SYSTEM_ERROR,
                f"执行命令失败: {command}\n{result.stdout}\n{result.stderr}",
            )
