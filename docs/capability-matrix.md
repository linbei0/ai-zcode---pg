# 双后端能力矩阵

## 状态说明

- `Java保留`：现有 Spring Boot 能力保留
- `Python已对齐`：FastAPI 后端已实现并可演示
- `Python待对齐`：后续再补

## 前端主链路

| 能力 | Java | Python |
| --- | --- | --- |
| 用户注册 `/user/register` | Java保留 | Python已对齐 |
| 用户登录 `/user/login` | Java保留 | Python已对齐 |
| 获取登录用户 `/user/get/login` | Java保留 | Python已对齐 |
| 退出登录 `/user/logout` | Java保留 | Python已对齐 |
| 创建应用 `/app/add` | Java保留 | Python已对齐 |
| 我的应用分页 `/app/my/list/page/vo` | Java保留 | Python已对齐 |
| 精选应用分页 `/app/good/list/page/vo` | Java保留 | Python已对齐 |
| 应用详情 `/app/get/vo` | Java保留 | Python已对齐 |
| 编辑应用 `/app/update` | Java保留 | Python已对齐 |
| 删除应用 `/app/delete` | Java保留 | Python已对齐 |
| 对话历史 `/chatHistory/app/{appId}` | Java保留 | Python已对齐 |
| SSE 生成 `/app/chat/gen/code` | Java保留 | Python已对齐 |
| 预览静态资源 `/static/{deployKey}/**` | Java保留 | Python已对齐 |
| 部署 `/app/deploy` | Java保留 | Python已对齐 |
| 下载 `/app/download/{appId}` | Java保留 | Python已对齐 |

## 管理后台

| 能力 | Java | Python |
| --- | --- | --- |
| 用户分页 `/user/list/page/vo` | Java保留 | Python已对齐 |
| 用户更新 `/user/update` | Java保留 | Python已对齐 |
| 用户删除 `/user/delete` | Java保留 | Python已对齐 |
| 应用分页 `/app/admin/list/page/vo` | Java保留 | Python已对齐 |
| 应用详情 `/app/admin/get/vo` | Java保留 | Python已对齐 |
| 应用更新 `/app/admin/update` | Java保留 | Python已对齐 |
| 应用删除 `/app/admin/delete` | Java保留 | Python已对齐 |
| 对话分页 `/chatHistory/admin/list/page/vo` | Java保留 | Python已对齐 |

## 额外接口

| 能力 | Java | Python |
| --- | --- | --- |
| 健康检查 `/health/` | Java保留 | Python已对齐 |
| 工作流路由 `/workflow/*` | Java保留 | Python部分对齐（测试辅助路由已提供） |
