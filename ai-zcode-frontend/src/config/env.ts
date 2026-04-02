/**
 * 环境变量配置
 */
const isDev = import.meta.env.DEV

// 应用部署域名
export const DEPLOY_DOMAIN = import.meta.env.VITE_DEPLOY_DOMAIN || 'http://localhost'

export const JAVA_API_BASE_URL =
  import.meta.env.VITE_JAVA_API_BASE_URL || (isDev ? '/api' : 'http://localhost:8234/api')

export const PYTHON_API_BASE_URL =
  import.meta.env.VITE_PYTHON_API_BASE_URL || (isDev ? '/py-api' : 'http://localhost:8335/api')

export const DEFAULT_BACKEND = (import.meta.env.VITE_DEFAULT_BACKEND || 'java') as
  | 'java'
  | 'python'
