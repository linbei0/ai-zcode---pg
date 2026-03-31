<template>
  <a-layout-header class="header">
    <a-row :wrap="false">
      <!-- 左侧：Logo和标题 -->
      <a-col flex="200px">
        <RouterLink to="/">
          <div class="header-left">
            <img class="logo" src="@/assets/logo.png" alt="Logo" />
            <h1 class="site-title">应用生成</h1>
          </div>
        </RouterLink>
      </a-col>
      <!-- 中间：导航菜单 -->
      <a-col flex="auto">
        <a-menu
          v-model:selectedKeys="selectedKeys"
          mode="horizontal"
          :items="menuItems"
          @click="handleMenuClick"
        />
      </a-col>
      <!-- 右侧：用户操作区域 -->
      <a-col>
        <div class="user-login-status">
          <a-select
            v-model:value="backendValue"
            class="backend-select"
            size="small"
            :options="backendOptions"
            @change="handleBackendChange"
          />
          <div v-if="loginUserStore.loginUser.id">
            <a-dropdown>
              <a-space>
                <a-avatar :src="loginUserStore.loginUser.userAvatar" />
                {{ loginUserStore.loginUser.userName ?? '无名' }}
              </a-space>
              <template #overlay>
                <a-menu>
                  <a-menu-item @click="doLogout">
                    <LogoutOutlined />
                    退出登录
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
          <div v-else>
            <a-button type="primary" href="/user/login">登录</a-button>
          </div>
        </div>
      </a-col>
    </a-row>
  </a-layout-header>
</template>

<script setup lang="ts">
import { computed, h, ref } from 'vue'
import { useRouter } from 'vue-router'
import { type MenuProps, message } from 'ant-design-vue'
import { useLoginUserStore } from '@/stores/loginUser.ts'
import { userLogout } from '@/api/userController.ts'
import { LogoutOutlined, HomeOutlined } from '@ant-design/icons-vue'
import {
  backendOptions,
  currentBackend,
  setCurrentBackend,
  type BackendType,
} from '@/config/backend'

const loginUserStore = useLoginUserStore()
const router = useRouter()
const backendValue = ref<BackendType>(currentBackend.value)
// 当前选中菜单
const selectedKeys = ref<string[]>(['/'])
// 监听路由变化，更新当前选中菜单
router.afterEach((to, from, next) => {
  selectedKeys.value = [to.path]
})

// 菜单配置项
const originItems = [
  {
    key: '/',
    icon: () => h(HomeOutlined),
    label: '主页',
    title: '主页',
  },
  {
    key: '/admin/userManage',
    label: '用户管理',
    title: '用户管理',
  },
  {
    key: '/admin/appManage',
    label: '应用管理',
    title: '应用管理',
  },
  {
    key: '/admin/chatManage',
    label: '对话管理',
    title: '对话管理',
  },
]

// 过滤菜单项
const filterMenus = (menus = [] as MenuProps['items']) => {
  return menus?.filter((menu) => {
    const menuKey = menu?.key as string
    if (menuKey?.startsWith('/admin')) {
      const loginUser = loginUserStore.loginUser
      if (!loginUser || loginUser.userRole !== 'admin') {
        return false
      }
    }
    return true
  })
}

// 展示在菜单的路由数组
const menuItems = computed<MenuProps['items']>(() => filterMenus(originItems))

// 处理菜单点击
const handleMenuClick: MenuProps['onClick'] = (e) => {
  const key = e.key as string
  selectedKeys.value = [key]
  // 跳转到对应页面
  if (key.startsWith('/')) {
    router.push(key)
  }
}

// 退出登录
const doLogout = async () => {
  const res = await userLogout()
  if (res.data.code === 0) {
    loginUserStore.setLoginUser({
      userName: '未登录',
    })
    message.success('退出登录成功')
    await router.push('/user/login')
  } else {
    message.error('退出登录失败，' + res.data.message)
  }
}

const handleBackendChange = (backend: BackendType) => {
  if (backend === currentBackend.value) {
    return
  }
  setCurrentBackend(backend)
  message.success(`已切换到 ${backend === 'python' ? 'Python' : 'Java'} 后端`)
  window.location.reload()
}
</script>

<style scoped>
.header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  padding: 0 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
  height: 48px;
  line-height: 48px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  transition: all 0.3s;
}

.header-left:hover {
  transform: translateY(-1px);
}

.logo {
  height: 32px;
  width: 32px;
  border-radius: 6px;
  box-shadow: 0 4px 15px rgba(79, 172, 254, 0.2);
  transition: all 0.3s;
}

.header-left:hover .logo {
  box-shadow: 0 6px 20px rgba(79, 172, 254, 0.3);
  transform: scale(1.05);
}

.site-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.user-login-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

.backend-select {
  width: 110px;
}

.user-login-status .ant-avatar {
  border: 2px solid rgba(79, 172, 254, 0.2);
  box-shadow: 0 4px 12px rgba(79, 172, 254, 0.15);
  transition: all 0.3s;
}

.user-login-status .ant-avatar:hover {
  border-color: rgba(79, 172, 254, 0.4);
  box-shadow: 0 6px 18px rgba(79, 172, 254, 0.25);
  transform: scale(1.05);
}

.user-login-status .ant-btn-primary {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border: none;
  border-radius: 12px;
  font-weight: 600;
  padding: 8px 24px;
  height: auto;
  box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
  transition: all 0.3s;
}

.user-login-status .ant-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(79, 172, 254, 0.4);
}

/* 菜单样式优化 */
:deep(.ant-menu-horizontal) {
  border-bottom: none !important;
  background: transparent !important;
  line-height: 48px !important;
}

:deep(.ant-menu-item) {
  border-radius: 12px !important;
  margin: 0 4px !important;
  transition: all 0.3s !important;
  color: #64748b !important;
  font-weight: 500 !important;
}

:deep(.ant-menu-item:hover) {
  background: rgba(79, 172, 254, 0.1) !important;
  color: #4facfe !important;
}

:deep(.ant-menu-item-selected) {
  background: linear-gradient(135deg, rgba(79, 172, 254, 0.15), rgba(0, 242, 254, 0.1)) !important;
  color: #4facfe !important;
  font-weight: 600 !important;
}

:deep(.ant-menu-item-selected::after) {
  display: none !important;
}

/* 下拉菜单样式 */
:deep(.ant-dropdown-menu) {
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(20px) !important;
  border-radius: 12px !important;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

:deep(.ant-dropdown-menu-item) {
  border-radius: 8px !important;
  margin: 4px !important;
  transition: all 0.3s !important;
}

:deep(.ant-dropdown-menu-item:hover) {
  background: rgba(79, 172, 254, 0.1) !important;
  color: #4facfe !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header {
    padding: 0 16px;
  }
  
  .site-title {
    font-size: 18px;
  }
  
  .logo {
    height: 44px;
    width: 44px;
  }
}
</style>
