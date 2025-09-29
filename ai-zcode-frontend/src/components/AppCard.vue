<template>
  <div class="app-card" :class="{ 'app-card--featured': featured }">
    <div class="app-preview">
      <img v-if="app.cover" :src="app.cover" :alt="app.appName" />
      <img v-else src="@/assets/aiAvatar.png" :alt="app.appName || '应用预览'" class="default-preview" />
      <div class="app-overlay">
        <a-space>
          <a-button type="primary" @click="handleViewChat">查看对话</a-button>
          <a-button v-if="app.deployKey" type="default" @click="handleViewWork">查看作品</a-button>
        </a-space>
      </div>
    </div>
    <div class="app-info">
      <div class="app-info-left">
        <a-avatar :src="app.user?.userAvatar" :size="40">
          {{ app.user?.userName?.charAt(0) || 'U' }}
        </a-avatar>
      </div>
      <div class="app-info-right">
        <h3 class="app-title">{{ app.appName || '未命名应用' }}</h3>
        <p class="app-author">
          {{ app.user?.userName || (featured ? '官方' : '未知用户') }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  app: API.AppVO
  featured?: boolean
}

interface Emits {
  (e: 'view-chat', appId: string | number | undefined): void
  (e: 'view-work', app: API.AppVO): void
}

const props = withDefaults(defineProps<Props>(), {
  featured: false,
})

const emit = defineEmits<Emits>()

const handleViewChat = () => {
  emit('view-chat', props.app.id)
}

const handleViewWork = () => {
  emit('view-work', props.app)
}
</script>

<style scoped>
.app-card {
  background: rgba(255, 255, 255, 0.98);
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.08),
    0 8px 25px rgba(255, 255, 255, 0.1) inset;
  backdrop-filter: blur(20px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.app-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #4facfe, #00f2fe);
  opacity: 0;
  transition: opacity 0.3s;
}

.app-card:hover::before {
  opacity: 1;
}

.app-card:hover {
  transform: translateY(-12px) scale(1.02);
  box-shadow: 
    0 30px 80px rgba(0, 0, 0, 0.12),
    0 12px 35px rgba(255, 255, 255, 0.15) inset;
  border-color: rgba(79, 172, 254, 0.4);
}

.app-card--featured {
  border-color: rgba(255, 215, 0, 0.4);
  box-shadow: 
    0 20px 60px rgba(255, 215, 0, 0.1),
    0 8px 25px rgba(255, 255, 255, 0.1) inset;
}

.app-card--featured::before {
  background: linear-gradient(90deg, #ffd700, #ffed4e);
}

.app-card--featured:hover {
  border-color: rgba(255, 215, 0, 0.6);
  box-shadow: 
    0 30px 80px rgba(255, 215, 0, 0.15),
    0 12px 35px rgba(255, 255, 255, 0.15) inset;
}

.app-preview {
  height: 200px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

.app-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.app-card:hover .app-preview img {
  transform: scale(1.1);
}

.default-preview {
  opacity: 0.8;
  filter: brightness(1.1) saturate(1.2);
}

.app-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(79, 172, 254, 0.9), rgba(0, 242, 254, 0.8));
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
}

.app-card:hover .app-overlay {
  opacity: 1;
}

.app-overlay .ant-btn {
  border-radius: 12px;
  font-weight: 600;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s;
}

.app-overlay .ant-btn-primary {
  background: rgba(255, 255, 255, 0.95);
  color: #4facfe;
  border-color: rgba(255, 255, 255, 0.5);
}

.app-overlay .ant-btn-primary:hover {
  background: white;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(255, 255, 255, 0.4);
}

.app-overlay .ant-btn-default {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border-color: rgba(255, 255, 255, 0.3);
}

.app-overlay .ant-btn-default:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(255, 255, 255, 0.2);
}

.app-info {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(10px);
}

.app-info-left {
  flex-shrink: 0;
}

.app-info-left .ant-avatar {
  border: 3px solid rgba(79, 172, 254, 0.2);
  box-shadow: 0 4px 15px rgba(79, 172, 254, 0.2);
  transition: all 0.3s;
}

.app-card:hover .app-info-left .ant-avatar {
  border-color: rgba(79, 172, 254, 0.4);
  box-shadow: 0 6px 20px rgba(79, 172, 254, 0.3);
  transform: scale(1.05);
}

.app-info-right {
  flex: 1;
  min-width: 0;
}

.app-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 6px;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.3s;
}

.app-card:hover .app-title {
  color: #4facfe;
}

.app-author {
  font-size: 14px;
  color: #64748b;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}

.app-card--featured .app-title {
  background: linear-gradient(135deg, #ffd700, #ffed4e);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.app-card--featured .app-author {
  color: #d97706;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-preview {
    height: 160px;
  }
  
  .app-info {
    padding: 20px;
    gap: 12px;
  }
  
  .app-title {
    font-size: 16px;
  }
}
</style>
