<template>
  <div class="home">
    <div class="header">
      <h1>商飞智能采购POC</h1>
    </div>
    <div class="content">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else class="projects-grid">
        <ProjectCard
          v-for="project in projects"
          :key="project.id"
          :project="project"
          @click="goToProject(project.id)"
          @delete="handleDeleteProject"
        />
        <div class="add-project-card" @click="handleAddProject">
          <div class="add-icon">+</div>
          <div class="add-text">创建项目</div>
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
  background-color: var(--bg-color);
}

.header {
  background: white;
  padding: 24px 32px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 32px;
}

.header h1 {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
}

.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 32px 32px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.add-project-card {
  min-height: 150px;
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  background-color: #fafafa;
}

.add-project-card:hover {
  border-color: var(--primary-color);
  background-color: #f0f9ff;
}

.add-icon {
  font-size: 48px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  line-height: 1;
}

.add-text {
  font-size: 14px;
  color: var(--text-secondary);
}

.loading,
.error {
  text-align: center;
  padding: 40px;
  font-size: 16px;
  color: var(--text-secondary);
}

.error {
  color: var(--danger-color);
}
</style>
