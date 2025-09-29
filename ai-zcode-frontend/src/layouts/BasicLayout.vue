<template>
  <a-layout class="basic-layout">
    <!-- 顶部导航栏 -->
    <GlobalHeader />
    <!-- 主要内容区域 -->
    <a-layout-content class="main-content">
      <router-view />
    </a-layout-content>
    <!-- 底部版权信息 -->
    <GlobalFooter />
  </a-layout>
</template>

<script setup lang="ts">
import GlobalHeader from '@/components/GlobalHeader.vue'
import GlobalFooter from '@/components/GlobalFooter.vue'
</script>

<style scoped>
.basic-layout {
  background: transparent;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  width: 100%;
  padding: 0;
  background: transparent;
  margin: 0;
  flex: 1;
  position: relative;
}

/* 确保内容区域有足够的最小高度 */
.main-content :deep(.ant-layout-content) {
  min-height: calc(100vh - 64px - 200px); /* 减去header和footer的高度 */
}

/* 响应式调整 */
@media (max-width: 768px) {
  .main-content :deep(.ant-layout-content) {
    min-height: calc(100vh - 56px - 180px);
  }
}
</style>
