<template>
  <div class="home">
    <!-- 顶部横幅区域 -->
    <div class="hero-section">
      <div class="hero-content">
        <div class="title-group">
          <h1 class="main-title">北研中心智能采购演示程序</h1>
          <h2 class="sub-title">Presented By: 数采智联队</h2>
        </div>
        <div class="hero-description">
          <p>智能化采购管理平台，提升采购效率，优化供应商管理</p>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <div class="content-header">
        <h3 class="section-title">项目管理</h3>
        <p class="section-description">创建和管理您的采购项目</p>
      </div>
      
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner"></div>
        <p class="loading-text">加载中...</p>
      </div>
      <div v-else-if="error" class="error-container">
        <div class="error-icon">⚠</div>
        <p class="error-text">{{ error }}</p>
      </div>
      <div v-else class="projects-section">
        <div class="projects-grid">
          <ProjectCard
            v-for="project in projects"
            :key="project.id"
            :project="project"
            @click="goToProject(project.id)"
            @delete="handleDeleteProject"
          />
          <div class="add-project-card" @click="handleAddProject">
            <div class="add-icon-wrapper">
              <div class="add-icon">+</div>
            </div>
            <div class="add-text">创建新项目</div>
            <div class="add-hint">点击开始新的采购项目</div>
          </div>
        </div>
        
        <div v-if="projects.length === 0" class="empty-state">
          <div class="empty-icon">📋</div>
          <p class="empty-text">暂无项目</p>
          <p class="empty-hint">点击右侧卡片创建您的第一个采购项目</p>
        </div>
      </div>
      
      <!-- 页脚信息 -->
      <div class="page-footer">
        <div class="footer-content">
          <div class="copyright">© {{ currentYear }} 北研中心. All rights reserved.</div>
          <div class="powered-by">Powered by: DeepSeek-v3.1</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getProjects, createProject, deleteProject } from '../api/project'
import ProjectCard from '../components/ProjectCard.vue'

export default {
  name: 'Home',
  components: {
    ProjectCard
  },
  setup() {
    const router = useRouter()
    const projects = ref([])
    const loading = ref(true)
    const error = ref('')
    const creating = ref(false)
    const currentYear = new Date().getFullYear()

    const fetchProjects = async () => {
      try {
        loading.value = true
        error.value = ''
        const data = await getProjects()
        projects.value = Array.isArray(data) ? data : []
      } catch (err) {
        error.value = err.message || '加载项目列表失败'
        console.error('Failed to fetch projects:', err)
      } finally {
        loading.value = false
      }
    }

    const goToProject = (id) => {
      router.push(`/project/${id}`)
    }

    const handleAddProject = async () => {
      try {
        creating.value = true
        error.value = ''
        const data = await createProject()
        // 创建成功后直接跳转到项目详情页
        router.push(`/project/${data.id}`)
      } catch (err) {
        error.value = err.message || '创建项目失败'
        console.error('Failed to create project:', err)
      } finally {
        creating.value = false
      }
    }

    const handleDeleteProject = async (projectId) => {
      // 确认删除
      if (!confirm('确定要删除这个项目吗？删除后将无法恢复。')) {
        return
      }
      
      try {
        error.value = ''
        await deleteProject(projectId)
        // 删除成功后刷新项目列表
        await fetchProjects()
      } catch (err) {
        error.value = err.message || '删除项目失败'
        console.error('Failed to delete project:', err)
      }
    }

    onMounted(() => {
      fetchProjects()
    })

    return {
      projects,
      loading,
      error,
      creating,
      currentYear,
      goToProject,
      handleAddProject,
      handleDeleteProject
    }
  }
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: linear-gradient(180deg, #f5f7fa 0%, #ffffff 100%);
}

/* 顶部横幅区域 */
.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 32px 32px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><defs><pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse"><path d="M 100 0 L 0 0 0 100" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
  opacity: 0.3;
}

.hero-content {
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.title-group {
  margin-bottom: 12px;
}

.main-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.sub-title {
  font-size: 18px;
  font-weight: 400;
  margin: 0;
  opacity: 0.95;
  letter-spacing: 0.5px;
}

.hero-description {
  margin-top: 16px;
  font-size: 16px;
  opacity: 0.9;
  line-height: 1.6;
}

.hero-description p {
  margin: 0;
}

/* 主要内容区域 */
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 48px 32px 64px;
}

.content-header {
  margin-bottom: 32px;
  text-align: center;
}

.section-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.section-description {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
}

/* 项目区域 */
.projects-section {
  margin-top: 40px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

/* 创建项目卡片 */
.add-project-card {
  min-height: 200px;
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);
  position: relative;
  overflow: hidden;
}

.add-project-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.3s;
}

.add-project-card:hover {
  border-color: var(--primary-color);
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
}

.add-project-card:hover::before {
  opacity: 1;
}

.add-icon-wrapper {
  position: relative;
  z-index: 1;
  margin-bottom: 16px;
}

.add-icon {
  font-size: 56px;
  color: var(--primary-color);
  line-height: 1;
  font-weight: 300;
  transition: transform 0.3s;
}

.add-project-card:hover .add-icon {
  transform: scale(1.1) rotate(90deg);
}

.add-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  position: relative;
  z-index: 1;
}

.add-hint {
  font-size: 13px;
  color: var(--text-secondary);
  position: relative;
  z-index: 1;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
}

/* 错误状态 */
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.error-text {
  font-size: 16px;
  color: var(--danger-color);
  margin: 0;
  text-align: center;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  margin-top: 24px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.empty-hint {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

/* 页脚 */
.page-footer {
  margin-top: 48px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
  color: var(--text-secondary);
}

.copyright {
  color: var(--text-secondary);
}

.powered-by {
  color: var(--text-secondary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .hero-section {
    padding: 24px 24px;
  }

  .main-title {
    font-size: 28px;
  }

  .sub-title {
    font-size: 16px;
  }

  .main-content {
    padding: 32px 24px 48px;
  }

  .projects-grid {
    grid-template-columns: 1fr;
  }

  .section-title {
    font-size: 24px;
  }

  .footer-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    font-size: 12px;
  }
}
</style>
