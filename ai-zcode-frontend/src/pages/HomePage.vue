<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useLoginUserStore } from '@/stores/loginUser'
import { addApp, listMyAppVoByPage, listGoodAppVoByPage } from '@/api/appController'
import { getDeployUrl } from '@/config/env'
import AppCard from '@/components/AppCard.vue'

const router = useRouter()
const loginUserStore = useLoginUserStore()

// 用户提示词
const userPrompt = ref('')
const creating = ref(false)

// 我的应用数据
const myApps = ref<API.AppVO[]>([])
const myAppsPage = reactive({
  current: 1,
  pageSize: 6,
  total: 0,
})

// 精选应用数据
const featuredApps = ref<API.AppVO[]>([])
const featuredAppsPage = reactive({
  current: 1,
  pageSize: 6,
  total: 0,
})

// 设置提示词
const setPrompt = (prompt: string) => {
  userPrompt.value = prompt
}

// 优化提示词功能已移除

// 创建应用
const createApp = async () => {
  if (!userPrompt.value.trim()) {
    message.warning('请输入应用描述')
    return
  }

  if (!loginUserStore.loginUser.id) {
    message.warning('请先登录')
    await router.push('/user/login')
    return
  }

  creating.value = true
  try {
    const res = await addApp({
      initPrompt: userPrompt.value.trim(),
    })

    if (res.data.code === 0 && res.data.data) {
      message.success('应用创建成功')
      // 跳转到对话页面，确保ID是字符串类型
      const appId = String(res.data.data)
      await router.push(`/app/chat/${appId}`)
    } else {
      message.error('创建失败：' + res.data.message)
    }
  } catch (error) {
    console.error('创建应用失败：', error)
    message.error('创建失败，请重试')
  } finally {
    creating.value = false
  }
}

// 加载我的应用
const loadMyApps = async () => {
  if (!loginUserStore.loginUser.id) {
    return
  }

  try {
    const res = await listMyAppVoByPage({
      pageNum: myAppsPage.current,
      pageSize: myAppsPage.pageSize,
      sortField: 'createTime',
      sortOrder: 'desc',
    })

    if (res.data.code === 0 && res.data.data) {
      myApps.value = res.data.data.records || []
      myAppsPage.total = res.data.data.totalRow || 0
    }
  } catch (error) {
    console.error('加载我的应用失败：', error)
  }
}

// 加载精选应用
const loadFeaturedApps = async () => {
  try {
    const res = await listGoodAppVoByPage({
      pageNum: featuredAppsPage.current,
      pageSize: featuredAppsPage.pageSize,
      sortField: 'createTime',
      sortOrder: 'desc',
    })

    if (res.data.code === 0 && res.data.data) {
      featuredApps.value = res.data.data.records || []
      featuredAppsPage.total = res.data.data.totalRow || 0
    }
  } catch (error) {
    console.error('加载精选应用失败：', error)
  }
}

// 查看对话
const viewChat = (appId: string | number | undefined) => {
  if (appId) {
    router.push(`/app/chat/${appId}?view=1`)
  }
}

// 查看作品
const viewWork = (app: API.AppVO) => {
  if (app.deployKey) {
    const url = getDeployUrl(app.deployKey)
    window.open(url, '_blank')
  }
}

// 格式化时间函数已移除，不再需要显示创建时间

// 页面加载时获取数据
onMounted(() => {
  loadMyApps()
  loadFeaturedApps()

  // 鼠标跟随光效
  const handleMouseMove = (e: MouseEvent) => {
    const { clientX, clientY } = e
    const { innerWidth, innerHeight } = window
    const x = (clientX / innerWidth) * 100
    const y = (clientY / innerHeight) * 100

    document.documentElement.style.setProperty('--mouse-x', `${x}%`)
    document.documentElement.style.setProperty('--mouse-y', `${y}%`)
  }

  document.addEventListener('mousemove', handleMouseMove)

  // 清理事件监听器
  return () => {
    document.removeEventListener('mousemove', handleMouseMove)
  }
})
</script>

<template>
  <div id="homePage">
    <div class="container">
      <!-- 网站标题和描述 -->
      <div class="hero-section">
        <h1 class="hero-title">AI 应用生成平台</h1>
        <p class="hero-description">一句话轻松创建网站应用</p>
      </div>

      <!-- 用户提示词输入框 -->
      <div class="input-section">
        <a-textarea
          v-model:value="userPrompt"
          placeholder="帮我创建个人博客网站"
          :rows="4"
          :maxlength="1000"
          class="prompt-input"
        />
        <div class="input-actions">
          <a-button type="primary" size="large" @click="createApp" :loading="creating">
            <template #icon>
              <span>↑</span>
            </template>
          </a-button>
        </div>
      </div>

      <!-- 快捷模板 -->
      <div class="quick-templates">
        <div class="template-buttons">
          <a-button 
            class="template-btn" 
            @click="setPrompt('创建一个现代化的企业官网，包含首页、关于我们、产品服务、新闻资讯、联系我们等页面，采用蓝色商务风格，响应式设计。')"
          >
            🏢 企业官网
          </a-button>
          <a-button 
            class="template-btn" 
            @click="setPrompt('开发一个在线商城网站，包含商品展示、购物车、用户登录、订单管理、支付功能，现代化电商设计风格。')"
          >
            🛒 在线商城
          </a-button>
          <a-button 
            class="template-btn" 
            @click="setPrompt('制作一个个人作品集网站，包含作品展示、项目介绍、个人简历、联系方式，极简设计风格突出作品展示。')"
          >
            🎨 作品展示
          </a-button>
          <a-button 
            class="template-btn" 
            @click="setPrompt('建设一个个人博客网站，包含文章发布、分类管理、评论系统、搜索功能，简洁优雅的阅读体验设计。')"
          >
            📝 个人博客
          </a-button>
          <a-button 
            class="template-btn" 
            @click="setPrompt('创建一个餐厅官网，包含菜单展示、在线预订、店铺介绍、联系信息，温馨美食主题设计风格。')"
          >
            🍽️ 餐厅官网
          </a-button>
          <a-button 
            class="template-btn" 
            @click="setPrompt('开发一个教育培训网站，包含课程展示、师资介绍、在线报名、学员评价，专业教育机构设计风格。')"
          >
            📚 教育培训
          </a-button>
        </div>
      </div>

      <!-- 我的作品 -->
      <div class="section">
        <h2 class="section-title">我的作品</h2>
        <div class="app-grid">
          <AppCard
            v-for="app in myApps"
            :key="app.id"
            :app="app"
            @view-chat="viewChat"
            @view-work="viewWork"
          />
        </div>
        <div class="pagination-wrapper">
          <a-pagination
            v-model:current="myAppsPage.current"
            v-model:page-size="myAppsPage.pageSize"
            :total="myAppsPage.total"
            :show-size-changer="false"
            :show-total="(total: number) => `共 ${total} 个应用`"
            @change="loadMyApps"
          />
        </div>
      </div>

      <!-- 精选案例 -->
      <div class="section">
        <h2 class="section-title">精选案例</h2>
        <div class="featured-grid">
          <AppCard
            v-for="app in featuredApps"
            :key="app.id"
            :app="app"
            :featured="true"
            @view-chat="viewChat"
            @view-work="viewWork"
          />
        </div>
        <div class="pagination-wrapper">
          <a-pagination
            v-model:current="featuredAppsPage.current"
            v-model:page-size="featuredAppsPage.pageSize"
            :total="featuredAppsPage.total"
            :show-size-changer="false"
            :show-total="(total: number) => `共 ${total} 个案例`"
            @change="loadFeaturedApps"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
#homePage {
  width: 100%;
  margin: 0;
  padding: 0;
  min-height: 100vh;
  background: transparent;
  position: relative;
  overflow: hidden;
}

/* 科技感装饰元素 */
#homePage::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(255, 255, 255, 0.06) 0%, transparent 50%);
  pointer-events: none;
  animation: floatingOrbs 15s ease-in-out infinite;
}

/* 动态光效 */
#homePage::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(
      600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%),
      rgba(255, 255, 255, 0.1) 0%,
      rgba(255, 255, 255, 0.05) 40%,
      transparent 80%
    );
  pointer-events: none;
  animation: lightPulse 8s ease-in-out infinite alternate;
}

@keyframes floatingOrbs {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -30px) scale(1.1);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.9);
  }
}

@keyframes lightPulse {
  0% {
    opacity: 0.3;
  }
  100% {
    opacity: 0.7;
  }
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 20px;
  position: relative;
  z-index: 2;
  width: 100%;
  box-sizing: border-box;
}

/* 英雄区域 */
.hero-section {
  text-align: center;
  padding: 100px 0 80px;
  margin-bottom: 60px;
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 800px;
  height: 400px;
  background: radial-gradient(ellipse, rgba(255, 255, 255, 0.15) 0%, transparent 70%);
  transform: translate(-50%, -50%);
  animation: heroGlow 10s ease-in-out infinite alternate;
}

@keyframes heroGlow {
  0% {
    opacity: 0.6;
    transform: translate(-50%, -50%) scale(1);
  }
  100% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1.05);
  }
}

.hero-title {
  font-size: 64px;
  font-weight: 800;
  margin: 0 0 24px;
  line-height: 1.1;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 50%, #e2e8f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -2px;
  position: relative;
  z-index: 2;
  text-shadow: 0 4px 20px rgba(255, 255, 255, 0.3);
  animation: titleFloat 6s ease-in-out infinite;
}

@keyframes titleFloat {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.hero-description {
  font-size: 24px;
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  position: relative;
  z-index: 2;
  font-weight: 300;
  letter-spacing: 0.5px;
}

/* 输入区域 */
.input-section {
  position: relative;
  margin: 0 auto 60px;
  max-width: 900px;
}

.prompt-input {
  border-radius: 20px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  font-size: 18px;
  padding: 24px 80px 24px 24px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.1),
    0 8px 25px rgba(255, 255, 255, 0.1) inset;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  color: #1e293b;
}

.prompt-input:focus {
  background: rgba(255, 255, 255, 1);
  border-color: rgba(255, 255, 255, 0.4);
  box-shadow: 
    0 25px 80px rgba(0, 0, 0, 0.15),
    0 0 0 4px rgba(255, 255, 255, 0.2);
  transform: translateY(-4px);
}

.prompt-input::placeholder {
  color: #94a3b8;
  font-style: italic;
}

.input-actions {
  position: absolute;
  bottom: 16px;
  right: 16px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.input-actions .ant-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
  font-size: 20px;
  font-weight: bold;
  box-shadow: 0 8px 25px rgba(79, 172, 254, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.input-actions .ant-btn:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 12px 35px rgba(79, 172, 254, 0.6);
}

/* 快捷模板区域 */
.quick-templates {
  margin-bottom: 60px;
}

.template-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
  max-width: 1000px;
  margin: 0 auto;
}

.template-btn {
  border-radius: 20px;
  padding: 12px 20px;
  height: auto;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #475569;
  backdrop-filter: blur(15px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  font-weight: 500;
  font-size: 14px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
}

.template-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(79, 172, 254, 0.1), transparent);
  transition: left 0.5s;
}

.template-btn:hover::before {
  left: 100%;
}

.template-btn:hover {
  background: rgba(255, 255, 255, 1);
  border-color: rgba(79, 172, 254, 0.4);
  color: #4facfe;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(79, 172, 254, 0.2);
}

/* 区域标题 */
.section {
  margin-bottom: 80px;
}

.section-title {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 40px;
  color: rgba(255, 255, 255, 0.95);
  text-align: center;
  text-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  position: relative;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: -12px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 4px;
  background: linear-gradient(90deg, #4facfe, #00f2fe);
  border-radius: 2px;
  box-shadow: 0 2px 10px rgba(79, 172, 254, 0.4);
}

/* 应用网格 */
.app-grid, .featured-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 32px;
  margin-bottom: 40px;
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 40px;
}

.pagination-wrapper :deep(.ant-pagination) {
  background: rgba(255, 255, 255, 0.9);
  padding: 16px 24px;
  border-radius: 16px;
  backdrop-filter: blur(20px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.pagination-wrapper :deep(.ant-pagination-item) {
  border: none;
  background: transparent;
  color: #475569;
  border-radius: 8px;
  transition: all 0.3s;
}

.pagination-wrapper :deep(.ant-pagination-item:hover) {
  background: rgba(79, 172, 254, 0.1);
  color: #4facfe;
}

.pagination-wrapper :deep(.ant-pagination-item-active) {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
  color: white;
  border: none;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .container {
    max-width: 100%;
    padding: 30px 16px;
  }
  
  .template-buttons {
    gap: 10px;
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 42px;
    letter-spacing: -1px;
  }

  .hero-description {
    font-size: 18px;
  }

  .hero-section {
    padding: 60px 0 50px;
  }

  .prompt-input {
    font-size: 16px;
    padding: 20px 70px 20px 20px;
  }

  .template-buttons {
    gap: 8px;
    max-width: 100%;
  }

  .template-btn {
    font-size: 13px;
    padding: 10px 16px;
  }

  .app-grid,
  .featured-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .section-title {
    font-size: 28px;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 32px;
  }

  .hero-description {
    font-size: 16px;
  }

  .container {
    padding: 20px 12px;
  }

  .template-buttons {
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }

  .template-btn {
    width: 200px;
    text-align: center;
  }
}
</style>
