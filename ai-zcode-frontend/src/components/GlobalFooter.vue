<template>
  <a-layout-footer class="footer">
    <div class="footer-content">
      <div class="footer-main">
        <div class="footer-brand">
          <h3 class="brand-title">AI 应用生成平台</h3>
          <p class="brand-description">让创意变为现实，让想法成为应用</p>
        </div>
        <div class="footer-links">
          <div class="link-group">
            <h4>产品</h4>
            <a href="#" class="footer-link">应用生成</a>
            <a href="#" class="footer-link">模板库</a>
            <a href="#" class="footer-link">部署服务</a>
          </div>
          <div class="link-group">
            <h4>支持</h4>
            <a href="#" class="footer-link">使用指南</a>
            <a href="#" class="footer-link">常见问题</a>
            <a href="#" class="footer-link">联系我们</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <p class="copyright">© 2025 AI应用生成平台. 让每个想法都能成为现实</p>
      </div>
    </div>
  </a-layout-footer>
</template>

<script setup lang="ts">
// 无需额外的响应式数据
</script>

<style scoped>
.footer {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  margin-top: 80px;
  padding: 0;
  position: relative;
}

.footer::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #4facfe, #00f2fe);
  opacity: 0.6;
}

.footer-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 60px 20px 30px;
}

.footer-main {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 60px;
  margin-bottom: 40px;
}

.footer-brand {
  text-align: left;
}

.brand-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 16px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.brand-description {
  font-size: 16px;
  color: #64748b;
  margin: 0;
  line-height: 1.6;
  font-weight: 400;
}

.footer-links {
  display: flex;
  gap: 40px;
  justify-content: flex-end;
}

.link-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.link-group h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px;
}

.footer-link {
  color: #64748b;
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s;
  font-weight: 500;
}

.footer-link:hover {
  color: #4facfe;
  transform: translateX(4px);
}

.footer-bottom {
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  padding-top: 30px;
  text-align: center;
}

.copyright {
  margin: 0;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 400;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .footer-content {
    padding: 40px 16px 20px;
  }
  
  .footer-main {
    grid-template-columns: 1fr;
    gap: 30px;
    text-align: center;
  }
  
  .footer-links {
    justify-content: center;
    gap: 30px;
  }
  
  .brand-title {
    font-size: 24px;
  }
  
  .brand-description {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .footer-links {
    flex-direction: column;
    gap: 20px;
  }
  
  .link-group {
    text-align: center;
  }
}
</style>
