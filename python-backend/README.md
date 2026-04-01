# AI-ZCode Python Backend

使用 `uv` + 虚拟环境管理的 FastAPI + LangChain Python 后端。

## 技术栈

- FastAPI
- LangChain / langchain-openai
- SQLAlchemy 2
- Alembic
- Redis Cookie Session
- Redis / 内存缓存
- 用户级限流
- Pydantic v2

## 快速开始

```bash
uv venv .venv
uv sync --all-groups
uv run uvicorn app.main:app --host 0.0.0.0 --port 8335 --reload
```

项目已提供本地开发配置文件 `python-backend/.env`，也可以基于 `python-backend/.env.example` 自行复制调整：

```bash
cp .env.example .env
```

## 默认环境变量

```bash
AIZCODE_DATABASE_URL=postgresql+psycopg://postgres:root@localhost:5432/ai_zcode
AIZCODE_REDIS_URL=redis://localhost:6379/0
AIZCODE_OPENAI_API_KEY=your-key
AIZCODE_OPENAI_MODEL=gpt-4.1-mini
AIZCODE_CODE_DEPLOY_HOST=http://localhost
AIZCODE_CORS_ORIGINS=["http://localhost:5173"]
```

## API 契约

- API 前缀：`/api`
- 健康检查：`/api/health/`
- SSE 生成：`/api/app/chat/gen/code`
- 工作流执行：`/api/workflow/execute`
- 工作流 Flux 流：`/api/workflow/execute-flux`
- 工作流 SSE 流：`/api/workflow/execute-sse`
- OpenAPI 文档：`/docs`

## 已对齐的工程化能力

- `workflow` 三接口
- 聊天生成用户级限流（默认 `5 次 / 60 秒`）
- 部署后自动生成封面资源并回写 `cover`
- 精选应用页缓存 + 应用详情缓存

## 运维说明

- PostgreSQL 与 Redis 需先启动
- Python 后端推荐使用 `uv` 启动
- `AIZCODE_PUBLIC_API_BASE_URL` 需要与前端访问 Python 后端的地址一致，否则封面资源 URL 会不正确
- 当前部署封面资源为服务端生成的 SVG 封面文件，路径由 `/api/static/covers/{file}` 提供

## 测试

```bash
uv run pytest
```
