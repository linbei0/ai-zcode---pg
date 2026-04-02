import pytest

from app.ai.parsers import extract_vue_project_files
from app.core.exceptions import BusinessException


def test_extract_vue_project_files_requires_core_files() -> None:
    content = """
FILE: README.md
```md
# Demo
```
FILE: src/assets/logo.svg
```svg
<svg></svg>
```
"""

    with pytest.raises(BusinessException, match="vue_project 模式至少需要"):
        extract_vue_project_files(content)


def test_extract_vue_project_files_accepts_valid_core_files() -> None:
    content = """
FILE: package.json
```json
{"name":"demo","private":true}
```
FILE: index.html
```html
<!DOCTYPE html><html><body><div id="app"></div></body></html>
```
FILE: src/main.js
```javascript
console.log('ok')
```
FILE: src/App.vue
```vue
<template><div>ok</div></template>
```
"""

    files = extract_vue_project_files(content)

    assert "package.json" in files
    assert "index.html" in files
    assert "src/main.js" in files
    assert "src/App.vue" in files


def test_extract_vue_project_files_accepts_minimal_app_source() -> None:
    content = """
FILE: src/App.vue
```vue
<template><div>ok</div></template>
```
"""

    files = extract_vue_project_files(content)

    assert files["src/App.vue"] == "<template><div>ok</div></template>"
