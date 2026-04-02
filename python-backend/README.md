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
uv run aizcode-dev
```

首次启动会自动下载并拉起开发环境所需的 `Nginx`，用于承载部署后的站点访问地址 `http://localhost/{deployKey}/`。

如果只想单独调试 FastAPI 而不自动管理 `Nginx`，可继续使用：

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8335 --reload
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
AIZCODE_ROUTING_OPENAI_MODEL=
AIZCODE_CODE_DEPLOY_HOST=http://localhost
AIZCODE_CORS_ORIGINS=["http://localhost:5173"]
AIZCODE_OPENAI_ENABLE_THINKING=
AIZCODE_NGINX_PORT=80
AIZCODE_NGINX_AUTO_START=true
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
- Vue 项目会先注入最小可运行脚手架，再由 AI 补充业务文件，降低工程文件缺失导致的构建失败
- Vue 项目在生成完成后会同步构建 `dist`，保证前端预览可用
- 部署后自动生成封面资源并回写 `cover`
- 精选应用页缓存 + 应用详情缓存

## 运维说明

- PostgreSQL 与 Redis 需先启动
- Python 后端推荐使用 `uv` 启动
- `uv run aizcode-dev` 会自动下载并启动开发环境的 `Nginx`
- `AIZCODE_PUBLIC_API_BASE_URL` 需要与前端访问 Python 后端的地址一致，否则封面资源 URL 会不正确
- 支持为“路由分类”单独配置模型；若路由模型是 Qwen，则结构化路由阶段会自动关闭 thinking，以兼容 DashScope 的 OpenAI 兼容接口限制
- 当前部署封面资源为服务端生成的 SVG 封面文件，路径由 `/api/static/covers/{file}` 提供

## 测试

```bash
uv run pytest
```
