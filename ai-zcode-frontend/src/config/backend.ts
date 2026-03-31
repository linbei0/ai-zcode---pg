import { ref } from 'vue'
import { CodeGenTypeEnum } from '@/utils/codeGenTypes'
import {
  DEFAULT_BACKEND,
  DEPLOY_DOMAIN,
  JAVA_API_BASE_URL,
  PYTHON_API_BASE_URL,
} from '@/config/env'

export type BackendType = 'java' | 'python'

const BACKEND_STORAGE_KEY = 'ai-zcode-backend'

const resolveInitialBackend = (): BackendType => {
  const stored = localStorage.getItem(BACKEND_STORAGE_KEY)
  if (stored === 'python') {
    return 'python'
  }
  return DEFAULT_BACKEND
}

export const currentBackend = ref<BackendType>(resolveInitialBackend())

export const backendOptions = [
  { label: 'Java', value: 'java' },
  { label: 'Python', value: 'python' },
]

export const getCurrentBackend = (): BackendType => currentBackend.value

export const setCurrentBackend = (backend: BackendType) => {
  currentBackend.value = backend
  localStorage.setItem(BACKEND_STORAGE_KEY, backend)
}

export const getApiBaseUrl = (backend: BackendType = currentBackend.value) => {
  return backend === 'python' ? PYTHON_API_BASE_URL : JAVA_API_BASE_URL
}

export const getStaticBaseUrl = (backend: BackendType = currentBackend.value) => {
  return `${getApiBaseUrl(backend)}/static`
}

export const getDeployUrl = (deployKey: string) => {
  return `${DEPLOY_DOMAIN}/${deployKey}`
}

export const getStaticPreviewUrl = (
  codeGenType: string,
  appId: string,
  backend: BackendType = currentBackend.value,
) => {
  const baseUrl = `${getStaticBaseUrl(backend)}/${codeGenType}_${appId}/`
  if (codeGenType === CodeGenTypeEnum.VUE_PROJECT) {
    return `${baseUrl}dist/index.html`
  }
  return baseUrl
}
