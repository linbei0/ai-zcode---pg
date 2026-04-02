from pathlib import Path
import tempfile

from app.core.config import build_settings
from app.services.storage_service import StorageService


def build_storage_service() -> StorageService:
    root = Path(tempfile.mkdtemp(prefix="aizcode-storage-"))
    settings = build_settings(
        {
            "repo_root": str(root),
            "testing": True,
            "redis_url": "redis://unused",
            "database_url": f"sqlite:///{root / 'test.db'}",
        }
    )
    return StorageService(settings)


def test_save_generated_vue_project_creates_scaffold_for_minimal_app_source() -> None:
    storage = build_storage_service()
    content = """
FILE: src/App.vue
```vue
<template><div>ok</div></template>
```
"""

    target_dir = storage.save_generated_code("vue_project", 1, content)
    package_json_path = target_dir / "package.json"
    index_html_path = target_dir / "index.html"
    main_js_path = target_dir / "src" / "main.js"
    vite_config_path = target_dir / "vite.config.js"

    assert package_json_path.exists()
    assert index_html_path.exists()
    assert main_js_path.exists()
    assert vite_config_path.exists()
    assert (target_dir / "src" / "router" / "index.js").exists()
    assert (target_dir / "src" / "views" / "Home.vue").exists()
    assert "<template><div>ok</div></template>" in (target_dir / "src" / "App.vue").read_text(encoding="utf-8")

    vite_config_content = vite_config_path.read_text(encoding="utf-8")
    assert "@vitejs/plugin-vue" in vite_config_content
    assert "defineConfig" in vite_config_content


def test_save_generated_vue_project_merges_vuex_dependency_and_store_bootstrap() -> None:
    storage = build_storage_service()
    content = """
FILE: src/App.vue
```vue
<template><div>{{ count }}</div></template>
<script setup>
import { computed } from 'vue'
import { useStore } from 'vuex'

const store = useStore()
const count = computed(() => store.state.count)
</script>
```
FILE: src/store/index.js
```javascript
import { createStore } from 'vuex'

export default createStore({
  state: {
    count: 1,
  },
})
```
"""

    target_dir = storage.save_generated_code("vue_project", 2, content)
    package_json_text = (target_dir / "package.json").read_text(encoding="utf-8")
    main_js_text = (target_dir / "src" / "main.js").read_text(encoding="utf-8")

    assert '"vuex"' in package_json_text
    assert "import store from './store'" in main_js_text
    assert "app.use(store)" in main_js_text
