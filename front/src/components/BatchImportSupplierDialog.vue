<template>
  <div class="dialog-overlay" @click.self="handleClose">
    <div class="dialog">
      <div class="dialog-header">批量导入供应商</div>
      <div class="dialog-body">
        <div class="form-group">
          <label class="form-label">选择投标文件 <span class="required">*</span></label>
          <input
            ref="fileInput"
            type="file"
            accept=".doc,.docx"
            multiple
            @change="handleFileChange"
            style="display: none"
          />
          <div class="file-upload">
            <button class="btn btn-primary" @click="triggerFileInput">选择文件</button>
            <span class="file-hint">可同时选择多个文件</span>
          </div>
          <div v-if="selectedFiles.length > 0" class="file-list">
            <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
              <span class="file-name">{{ file.name }}</span>
              <button class="btn-remove" @click="removeFile(index)">×</button>
            </div>
          </div>
          <div v-else class="file-placeholder">未选择文件</div>
          <div v-if="errors.files" class="form-error">{{ errors.files }}</div>
        </div>
        <div v-if="submitError" class="form-error">{{ submitError }}</div>
        <div v-if="importResult" class="import-result">
          <div class="result-header">导入结果：</div>
          <div class="result-summary">
            共处理 {{ importResult.total_files }} 个文件，成功启动 {{ importResult.processed_files }} 个识别任务
          </div>
          <div v-if="importResult.results && importResult.results.length > 0" class="result-details">
            <div v-for="(result, index) in importResult.results" :key="index" class="result-item">
              <span class="result-file-name">{{ result.file_name }}</span>
              <span :class="['result-status', `status-${result.status}`]">
                {{ getStatusText(result.status) }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <div class="dialog-footer">
        <button class="btn" @click="handleClose">关闭</button>
        <button 
          class="btn btn-primary" 
          @click="handleSubmit" 
          :disabled="submitting || selectedFiles.length === 0"
        >
          {{ submitting ? '导入中...' : '开始导入' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { batchImportSuppliers } from '../api/supplier'

export default {
  name: 'BatchImportSupplierDialog',
  props: {
    projectId: {
      type: Number,
      required: true
    }
  },
  emits: ['close', 'success'],
  setup(props, { emit }) {
    const fileInput = ref(null)
    const selectedFiles = ref([])
    const submitting = ref(false)
    const submitError = ref('')
    const importResult = ref(null)
    
    const errors = reactive({
      files: ''
    })

    const validate = () => {
      let valid = true
      errors.files = ''

      if (selectedFiles.value.length === 0) {
        errors.files = '请至少选择一个文件'
        valid = false
      }

      // 验证文件类型
      for (const file of selectedFiles.value) {
        const ext = file.name.split('.').pop().toLowerCase()
        if (!['doc', 'docx'].includes(ext)) {
          errors.files = '所有文件必须是 .doc 或 .docx 格式'
          valid = false
          break
        }
      }

      return valid
    }

    const handleFileChange = (event) => {
      const files = Array.from(event.target.files)
      console.log(`[批量导入对话框] 选择了 ${files.length} 个文件`)
      files.forEach((file, index) => {
        console.log(`[批量导入对话框] 文件 ${index + 1}: ${file.name}`)
      })
      if (files.length > 0) {
        selectedFiles.value = files
        errors.files = ''
        importResult.value = null
      }
    }

    const removeFile = (index) => {
      selectedFiles.value.splice(index, 1)
      importResult.value = null
    }

    const triggerFileInput = () => {
      fileInput.value?.click()
    }

    const getStatusText = (status) => {
      const statusMap = {
        'processing': '处理中',
        'skipped': '已跳过',
        'error': '错误'
      }
      return statusMap[status] || status
    }

    const handleClose = () => {
      emit('close')
    }

    const handleSubmit = async () => {
      if (!validate()) {
        return
      }

      try {
        submitting.value = true
        submitError.value = ''
        importResult.value = null
        
        // 调用批量导入 API，等待请求返回
        await batchImportSuppliers(props.projectId, selectedFiles.value)
        
        // 请求成功返回后，关闭对话框并刷新供应商列表
        emit('close')
        emit('success')
      } catch (err) {
        // 请求失败，显示错误信息，不关闭对话框
        submitError.value = err.response?.data?.detail || err.message || '批量导入失败'
      } finally {
        submitting.value = false
      }
    }

    return {
      fileInput,
      selectedFiles,
      errors,
      submitting,
      submitError,
      importResult,
      handleFileChange,
      removeFile,
      triggerFileInput,
      getStatusText,
      handleClose,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.required {
  color: var(--danger-color);
}

.file-upload {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.file-hint {
  color: var(--text-secondary);
  font-size: 13px;
}

.file-list {
  margin-top: 12px;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px;
  margin-bottom: 4px;
  background: var(--bg-secondary);
  border-radius: 4px;
}

.file-item:last-child {
  margin-bottom: 0;
}

.file-name {
  color: var(--text-primary);
  font-size: 14px;
  flex: 1;
  word-break: break-word;
}

.btn-remove {
  background: transparent;
  border: none;
  color: var(--danger-color);
  font-size: 20px;
  cursor: pointer;
  padding: 0 8px;
  line-height: 1;
}

.btn-remove:hover {
  opacity: 0.7;
}

.file-placeholder {
  color: var(--text-secondary);
  font-size: 14px;
  padding: 12px;
  text-align: center;
}

.import-result {
  margin-top: 20px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 4px;
}

.result-header {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.result-summary {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 12px;
}

.result-details {
  margin-top: 12px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  margin-bottom: 4px;
  background: var(--bg-primary);
  border-radius: 4px;
}

.result-file-name {
  color: var(--text-primary);
  font-size: 14px;
  flex: 1;
  word-break: break-word;
}

.result-status {
  font-size: 13px;
  padding: 4px 8px;
  border-radius: 4px;
}

.status-processing {
  background: var(--info-color);
  color: white;
}

.status-skipped {
  background: var(--warning-color);
  color: white;
}

.status-error {
  background: var(--danger-color);
  color: white;
}
</style>

