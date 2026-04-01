import { useLoginUserStore } from '@/stores/loginUser'
import { message } from 'ant-design-vue'
import router from '@/router'

// 是否为首次获取登录用户
let firstFetchLoginUser = true
let fetchLoginUserPromise: Promise<void> | null = null

/**
 * 初始化登录态。
 * 公开页面不阻塞路由，管理页面按需等待，避免后端超时时登录页也无法进入。
 */
const ensureLoginUserFetched = (loginUserStore: ReturnType<typeof useLoginUserStore>) => {
  if (!firstFetchLoginUser) {
    return fetchLoginUserPromise ?? Promise.resolve()
  }
  if (!fetchLoginUserPromise) {
    fetchLoginUserPromise = loginUserStore
      .fetchLoginUser()
      .catch(() => {
        console.warn('首次获取登录用户失败，将按未登录状态继续')
      })
      .finally(() => {
        firstFetchLoginUser = false
      })
  }
  return fetchLoginUserPromise
}

/**
 * 全局权限校验
 */
router.beforeEach(async (to, from, next) => {
  const loginUserStore = useLoginUserStore()
  let loginUser = loginUserStore.loginUser
  const toUrl = to.fullPath
  const isAuthPage = toUrl.startsWith('/user/login') || toUrl.startsWith('/user/register')
  // 确保页面刷新，首次加载时，能够等后端返回用户信息后再校验权限
  if (firstFetchLoginUser && !isAuthPage) {
    if (toUrl.startsWith('/admin')) {
      await ensureLoginUserFetched(loginUserStore)
      loginUser = loginUserStore.loginUser
    } else {
      void ensureLoginUserFetched(loginUserStore)
    }
  }
  if (toUrl.startsWith('/admin')) {
    if (!loginUser || loginUser.userRole !== 'admin') {
      message.error('没有权限')
      next(`/user/login?redirect=${to.fullPath}`)
      return
    }
  }
  next()
})
