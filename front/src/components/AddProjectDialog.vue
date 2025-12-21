<template>
  <div class="dialog-overlay" @click.self="handleClose">
    <div class="dialog">
      <div class="dialog-header">创建新项目</div>
      <div class="dialog-body">
        <div class="form-group">
          <label class="form-label">上传采购征询文件 <span class="required">*</span></label>
          <input
            ref="fileInput"
            type="file"
            accept=".doc,.docx"
            @change="handleFileChange"
            style="display: none"
          />
          <div class="file-upload">
            <button class="btn btn-primary" @click="triggerFileInput">选择文件</button>
            <span v-if="selectedFile" class="file-name">{{ selectedFile.name }}</span>
            <span v-else class="file-placeholder">未选择文件</span>
          </div>
          <div v-if="errors.file" class="form-error">{{ errors.file }}</div>
          <div class="file-hint">支持 .doc 或 .docx 格式</div>
        </div>
        <div class="form-group">
          <label class="form-label">上传需求文档</label>
          <input
            ref="businessRequirementInput"
            type="file"
            accept=".doc,.docx"
            @change="handleBusinessRequirementChange"
            style="display: none"
          />
          <div class="file-upload">
            <button class="btn btn-primary" @click="triggerBusinessRequirementInput">选择文件</button>
            <span v-if="selectedBusinessRequirementFile" class="file-name">{{ selectedBusinessRequirementFile.name }}</span>
            <span v-else class="file-placeholder">未选择文件</span>
          </div>
          <div class="file-hint">支持 .doc 或 .docx 格式（可选）</div>
        </div>
        <div class="form-group">
          <label class="form-label">上传采购部门规范文档</label>
          <input
            ref="procurementRequirementInput"
            type="file"
            accept=".doc,.docx"
            @change="handleProcurementRequirementChange"
            style="display: none"
          />
          <div class="file-upload">
            <button class="btn btn-primary" @click="triggerProcurementRequirementInput">选择文件</button>
            <span v-if="selectedProcurementRequirementFile" class="file-name">{{ selectedProcurementRequirementFile.name }}</span>
            <span v-else class="file-placeholder">未选择文件</span>
          </div>
          <div class="file-hint">支持 .doc 或 .docx 格式（可选）</div>
        </div>
        <div class="form-group">
          <label class="form-label">项目名称 <span class="required">*</span></label>
          <input
            v-model="form.name"
            type="text"
            class="input"
            placeholder="请输入项目名称"
          />
          <div v-if="errors.name" class="form-error">{{ errors.name }}</div>
        </div>
        <div v-if="submitError" class="form-error">{{ submitError }}</div>
      </div>
      <div class="dialog-footer">
        <button class="btn" @click="handleClose">取消</button>
        <button class="btn btn-primary" @click="handleSubmit" :disabled="submitting">
          {{ submitting ? '创建中...' : '创建' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { createProject } from '../api/project'

export default {
  name: 'AddProjectDialog',
  emits: ['close', 'success'],
  setup(props, { emit }) {
    const fileInput = ref(null)
    const businessRequirementInput = ref(null)
    const procurementRequirementInput = ref(null)
    const selectedFile = ref(null)
    const selectedBusinessRequirementFile = ref(null)
    const selectedProcurementRequirementFile = ref(null)
    const submitting = ref(false)
    const submitError = ref('')
    
    const form = reactive({
      name: ''
    })
    
    const errors = reactive({
      name: '',
      file: ''
    })

    const validate = () => {
      let valid = true
      errors.name = ''
      errors.file = ''

      if (!form.name.trim()) {
        errors.name = '请输入项目名称'
        valid = false
      }

      if (!selectedFile.value) {
        errors.file = '请上传采购征询文件'
        valid = false
      } else {
        const ext = selectedFile.value.name.split('.').pop().toLowerCase()
        if (!['doc', 'docx'].includes(ext)) {
          errors.file = '采购征询文件必须是 .doc 或 .docx 格式'
          valid = false
        }
      }

      return valid
    }

    const handleFileChange = (event) => {
      const file = event.target.files[0]
      if (file) {
        selectedFile.value = file
        errors.file = ''
      }
    }

    const handleBusinessRequirementChange = (event) => {
      const file = event.target.files[0]
      if (file) {
        selectedBusinessRequirementFile.value = file
      }
    }

    const handleProcurementRequirementChange = (event) => {
      const file = event.target.files[0]
      if (file) {
        selectedProcurementRequirementFile.value = file
      }
    }

    const triggerFileInput = () => {
      fileInput.value?.click()
    }

    const triggerBusinessRequirementInput = () => {
      businessRequirementInput.value?.click()
    }

    const triggerProcurementRequirementInput = () => {
      procurementRequirementInput.value?.click()
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
        
        await createProject(
          form.name.trim(),
          selectedFile.value,
          selectedBusinessRequirementFile.value,
          selectedProcurementRequirementFile.value
        )
        
        emit('success')
      } catch (err) {
        submitError.value = err.message || '创建项目失败'
      } finally {
        submitting.value = false
      }
    }

    return {
      fileInput,
      businessRequirementInput,
      procurementRequirementInput,
      selectedFile,
      selectedBusinessRequirementFile,
      selectedProcurementRequirementFile,
      form,
      errors,
      submitting,
      submitError,
      handleFileChange,
      handleBusinessRequirementChange,
      handleProcurementRequirementChange,
      triggerFileInput,
      triggerBusinessRequirementInput,
      triggerProcurementRequirementInput,
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
}

.file-name {
  color: var(--text-primary);
  font-size: 14px;
}

.file-placeholder {
  color: var(--text-secondary);
  font-size: 14px;
}

.file-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}
</style>
