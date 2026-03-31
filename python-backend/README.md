# AI-ZCode Python Backend

使用 `uv` + 虚拟环境管理的 FastAPI + LangChain Python 后端。

## 技术栈

- FastAPI
- LangChain / langchain-openai
- SQLAlchemy 2
- Alembic
- Redis Cookie Session
- Pydantic v2

## 快速开始

```bash
uv venv .venv
uv sync --all-groups
uv run uvicorn app.main:app --host 0.0.0.0 --port 8335 --reload
```

## 默认环境变量

```bash
AIZCODE_DATABASE_URL=postgresql+psycopg://postgres:root@localhost:5432/ai_zcode
AIZCODE_REDIS_URL=redis://localhost:6379/0
AIZCODE_OPENAI_API_KEY=your-key
AIZCODE_OPENAI_MODEL=gpt-4.1-mini
AIZCODE_CODE_DEPLOY_HOST=http://localhost
```

## API 契约

- API 前缀：`/api`
- 健康检查：`/api/health/`
- SSE 生成：`/api/app/chat/gen/code`
- OpenAPI 文档：`/docs`

## 测试

```bash
uv run pytest
```
