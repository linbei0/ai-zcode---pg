from __future__ import annotations

import json
import re
import shutil
import subprocess
import zipfile
from io import BytesIO
from pathlib import Path

from app.ai.parsers import extract_html, extract_multi_file, extract_vue_project_files
from app.core.config import Settings
from app.core.exceptions import BusinessException, ErrorCode

IMPORT_FROM_PATTERN = re.compile(r"from\s+['\"](?P<module>[^'\"]+)['\"]")
DIRECT_IMPORT_PATTERN = re.compile(r"import\s+['\"](?P<module>[^'\"]+)['\"]")
NPM_PACKAGE_NAME_PATTERN = re.compile(r"^(?P<name>@?[^/]+(?:/[^/]+)?)")
PACKAGE_DEFAULT_VERSIONS = {
    "vuex": "^4.1.0",
    "pinia": "^2.1.7",
    "axios": "^1.7.2",
}


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
            vue_project_files = extract_vue_project_files(content)
            vue_project_files = self._build_vue_project_files(vue_project_files)
            for relative_path, file_content in vue_project_files.items():
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

    def _build_vue_project_files(self, files: dict[str, str]) -> dict[str, str]:
        scaffold_files = self._create_vue_project_scaffold()
        scaffold_files.update(files)
        scaffold_files = self._merge_vue_package_dependencies(scaffold_files)
        scaffold_files = self._normalize_vue_router_history(scaffold_files)
        scaffold_files = self._inject_vue_runtime_bootstrap(scaffold_files)
        return scaffold_files

    def _create_vue_project_scaffold(self) -> dict[str, str]:
        return {
            "package.json": """{
  "name": "ai-zcode-vue-project",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.21",
    "vue-router": "^4.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.4",
    "vite": "^5.2.8"
  }
}
""".strip(),
            "index.html": """<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI ZCode Vue Project</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
""".strip(),
            "vite.config.js": """import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: './',
  plugins: [vue()],
})
""".strip(),
            "src/main.js": """import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(router)
app.mount('#app')
""".strip(),
            "src/App.vue": """<template>
  <router-view />
</template>
""".strip(),
            "src/router/index.js": """import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/Home.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
  ],
})

export default router
""".strip(),
            "src/views/Home.vue": """<template>
  <main>
    <h1>AI ZCode Vue Project</h1>
  </main>
</template>
""".strip(),
        }

    def _merge_vue_package_dependencies(self, files: dict[str, str]) -> dict[str, str]:
        package_json = json.loads(files["package.json"])
        dependencies = dict(package_json.get("dependencies") or {})
        dev_dependencies = dict(package_json.get("devDependencies") or {})

        for file_path, content in files.items():
            if not file_path.endswith((".js", ".ts", ".vue")):
                continue
            for package_name in self._extract_external_packages(content):
                if package_name in dependencies or package_name in dev_dependencies:
                    continue
                default_version = PACKAGE_DEFAULT_VERSIONS.get(package_name)
                if default_version:
                    dependencies[package_name] = default_version

        package_json["dependencies"] = dependencies
        package_json["devDependencies"] = dev_dependencies
        files["package.json"] = json.dumps(package_json, ensure_ascii=False, indent=2) + "\n"
        return files

    def _inject_vue_runtime_bootstrap(self, files: dict[str, str]) -> dict[str, str]:
        main_entry_path = "src/main.js" if "src/main.js" in files else "src/main.ts" if "src/main.ts" in files else None
        if main_entry_path is None:
            return files

        main_entry_content = files[main_entry_path]

        if "src/store/index.js" in files or "src/store/index.ts" in files:
            main_entry_content = self._ensure_store_bootstrap(main_entry_content)

        if "src/pinia/index.js" in files or "src/pinia/index.ts" in files:
            main_entry_content = self._ensure_pinia_bootstrap(main_entry_content)

        files[main_entry_path] = main_entry_content
        return files

    def _normalize_vue_router_history(self, files: dict[str, str]) -> dict[str, str]:
        for router_path in ("src/router/index.js", "src/router/index.ts"):
            if router_path not in files:
                continue
            router_content = files[router_path]
            normalized_content = router_content.replace("createWebHistory", "createWebHashHistory")
            normalized_content = normalized_content.replace("createMemoryHistory", "createWebHashHistory")
            files[router_path] = normalized_content
        return files

    def _ensure_store_bootstrap(self, main_entry_content: str) -> str:
        normalized_content = main_entry_content
        if "import store from './store'" not in normalized_content and 'import store from "./store"' not in normalized_content:
            normalized_content = "import store from './store'\n" + normalized_content
        if "app.use(store)" not in normalized_content:
            normalized_content = normalized_content.replace("app.use(router)\n", "app.use(router)\napp.use(store)\n")
        return normalized_content

    def _ensure_pinia_bootstrap(self, main_entry_content: str) -> str:
        normalized_content = main_entry_content
        if "import { createPinia } from 'pinia'" not in normalized_content and 'import { createPinia } from "pinia"' not in normalized_content:
            normalized_content = "import { createPinia } from 'pinia'\n" + normalized_content
        if "const pinia = createPinia()" not in normalized_content:
            normalized_content = normalized_content.replace("const app = createApp(App)\n", "const app = createApp(App)\nconst pinia = createPinia()\n")
        if "app.use(pinia)" not in normalized_content:
            normalized_content = normalized_content.replace("app.use(router)\n", "app.use(router)\napp.use(pinia)\n")
        return normalized_content

    def _extract_external_packages(self, content: str) -> set[str]:
        package_names: set[str] = set()
        for pattern in (IMPORT_FROM_PATTERN, DIRECT_IMPORT_PATTERN):
            for match in pattern.finditer(content):
                module_name = match.group("module").strip()
                if module_name.startswith((".", "/")):
                    continue
                package_match = NPM_PACKAGE_NAME_PATTERN.match(module_name)
                if not package_match:
                    continue
                package_names.add(package_match.group("name"))
        return package_names
