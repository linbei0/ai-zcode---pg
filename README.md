# AI-ZCode 项目 README

AI-ZCode 是一个基于前后端分离架构的 AI 代码生成平台。后端使用 Spring Boot 3 + Java 21，前端使用 Vue 3 + Vite，数据库使用 PostgreSQL，缓存使用 Redis。项目集成了 LangChain4j 与多模型支持，并提供基于工作流的代码生成能力。

## 目录
- 项目结构
- 技术栈
- 前置依赖
- 快速开始
  - 数据库初始化（PostgreSQL）
  - 后端启动
  - 前端启动
- 配置说明
- 常用访问地址

## 项目结构
```
ai-zcode - pg/
├── ai-zcode-frontend/       # 前端（Vue 3 + Vite）
├── src/                     # 后端（Spring Boot）
│   ├── main/java/com/aizcode # 后端源码
│   └── main/resources        # 配置、Mapper XML 等
├── sql/                     # 数据库脚本
│   ├── create_table_postgresql.sql
├── pom.xml                  # 后端 Maven 配置
└── README.md                # 项目说明
```

## 技术栈
- 后端：Spring Boot 3.5.x、Java 21、MyBatis-Flex、HikariCP
- AI：LangChain4j、LangGraph4j、OpenAI、阿里云 DashScope
- 前端：Vue 3、TypeScript、Vite、Ant Design Vue、Pinia、Vue Router
- 数据库：PostgreSQL
- 缓存：Redis + Caffeine
- 文档：SpringDoc + Knife4j
- 监控：Actuator、Prometheus、Grafana

## 前置依赖
- Java 21（JDK 21）
- Maven（已提供 `mvnw.cmd` 可直接使用）
- Node.js 20+ 与 npm
- PostgreSQL 14+（默认端口 5432）
- Redis（默认端口 6379）
- 可选：Chrome（网页截图，WebDriverManager 会自动下载驱动）

## 快速开始

### 1) 数据库初始化（PostgreSQL）
1. 创建数据库并初始化表与触发器：
   - 执行 `sql/create_table_postgresql.sql`
   - 执行 `sql/fix_trigger_function.sql`

示例命令（在 pgAdmin 或 psql 里执行）：
```sql
-- 执行建表
\i 'E:/java-project/ai-zcode - pg/sql/create_table_postgresql.sql'
```

> 重要：本项目的所有数据库字段名采用下划线命名（snake_case），如 `create_time`、`update_time`、`user_account`。

### 2) 后端启动
1. 配置 `src/main/resources/application.yml`（默认示例）：
```yaml
spring:
  datasource:
    driver-class-name: org.postgresql.Driver
    url: jdbc:postgresql://localhost:5432/ai_zcode
    username: postgres
    password: <你的密码>
  data:
    redis:
      host: localhost
      port: 6379
      database: 0
      password: 
server:
  port: 8234
  servlet:
    context-path: /api
springdoc:
  group-configs:
    - group: 'default'
      packages-to-scan: com.aizcode.controller
knife4j:
  enable: true
  setting:
    language: zh_cn
management:
  endpoints:
    web:
      exposure:
        include: health,info,prometheus
  endpoint:
    health:
      show-details: always
```

2. 启动后端（Windows PowerShell）：
```powershell
# 在项目根目录
./mvnw.cmd spring-boot:run
```

### 3) 前端启动
```powershell
cd "ai-zcode-frontend"
npm install
npm run dev
```
Vite 开发服务器默认运行在 `http://localhost:5173/`，已配置代理将以 `/api` 开头的请求转发到后端 `http://localhost:8234`。

## 配置说明
- 数据源：`application.yml` 中的 `spring.datasource` 需要指向 PostgreSQL。
- Redis：`spring.data.redis` 用于会话与缓存。
- AI 模型：根据使用的模型配置对应的环境变量，例如：
  - `OPENAI_API_KEY`
  - `DASHSCOPE_API_KEY`
- 对象存储（可选）：若使用腾讯云 COS，请在 `CosClientConfig` 对应位置配置：
  - `COS_SECRET_ID`、`COS_SECRET_KEY`、`COS_REGION`、`COS_BUCKET`

## 常用访问地址
- 前端（开发）：`http://localhost:5173/`
- 后端 API 根路径：`http://localhost:8234/api`
- API 文档（Knife4j）：`http://localhost:8234/api/doc.html`
- 健康检查（Actuator）：`http://localhost:8234/api/actuator/health`
- 监控指标（Prometheus）：`http://localhost:8234/api/actuator/prometheus`