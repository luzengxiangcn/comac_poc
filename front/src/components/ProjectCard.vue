<template>
  <div class="project-card card" @click="$emit('click')">
    <div class="project-header">
    <div class="project-name">{{ project.name }}</div>
      <button 
        class="delete-btn" 
        @click.stop="$emit('delete', project.id)"
        title="删除项目"
      >
        ×
      </button>
    </div>
    <div class="project-info">
      <span class="supplier-count">供应商：{{ supplierCount }}个</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProjectCard',
  props: {
    project: {
      type: Object,
      required: true
    }
  },
  computed: {
    supplierCount() {
      return this.project.supplier_count || this.project.bid_count || 0
    }
  }
}
</script>

<style scoped>
.project-card {
  padding: 24px;
  cursor: pointer;
  transition: transform 0.2s;
}

.project-card:hover {
  transform: translateY(-4px);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 8px;
}

.project-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  word-break: break-word;
  flex: 1;
}

.delete-btn {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border: none;
  background-color: transparent;
  color: var(--text-secondary);
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  padding: 0;
}

.delete-btn:hover {
  background-color: rgba(255, 0, 0, 0.1);
  color: #ff4444;
}

.project-info {
  display: flex;
  align-items: center;
  color: var(--text-secondary);
  font-size: 14px;
}

.supplier-count {
  padding: 4px 12px;
  background-color: var(--bg-color);
  border-radius: 12px;
}
</style>
