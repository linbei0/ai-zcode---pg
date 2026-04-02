/**
 * 环境变量配置说明
 *
 * 在项目根目录创建 .env.local 或 .env.development 文件，并添加以下配置：
 *
 * # 应用部署域名
 * VITE_DEPLOY_DOMAIN=http://localhost
 *
 * # Java API 基础地址
 * # 本地开发建议通过 Vite 代理使用 /api
 * VITE_JAVA_API_BASE_URL=/api
 *
 * # Python API 基础地址
 * # 本地开发建议通过 Vite 代理使用 /py-api
 * VITE_PYTHON_API_BASE_URL=/py-api
 *
 * # 默认后端
 * VITE_DEFAULT_BACKEND=java
 *
 * 生产环境可以创建 .env.production 文件：
 *
 * # 生产环境配置示例
 * VITE_DEPLOY_DOMAIN=https://your-domain.com
 * VITE_JAVA_API_BASE_URL=https://java-api.your-domain.com
 * VITE_PYTHON_API_BASE_URL=https://python-api.your-domain.com
 */

export {}
