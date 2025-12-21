<template>
  <div class="dialog-overlay" @click.self="handleClose">
    <div class="dialog">
      <div class="dialog-header">添加供应商</div>
      <div class="dialog-body">
        <div class="form-group">
          <label class="form-label">供应商名称 <span class="required">*</span></label>
          <input
            v-model="form.name"
            type="text"
            class="input"
            placeholder="请输入供应商名称"
          />
          <div v-if="errors.name" class="form-error">{{ errors.name }}</div>
        </div>
        <div class="form-group">
          <label class="form-label">社会信用代码 <span class="required">*</span></label>
          <input
            v-model="form.registrationNumber"
            type="text"
            class="input"
            placeholder="请输入社会信用代码"
          />
          <div v-if="errors.registrationNumber" class="form-error">{{ errors.registrationNumber }}</div>
        </div>
        <div class="form-group">
          <label class="form-label">上传投标文件（可选）</label>
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
        </div>
        <div v-if="submitError" class="form-error">{{ submitError }}</div>
      </div>
      <div class="dialog-footer">
        <button class="btn" @click="handleClose">取消</button>
        <button class="btn btn-primary" @click="handleSubmit" :disabled="submitting">
          {{ submitting ? '提交中...' : '确定' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { createBidRecord } from '../api/bid'

export default {
  name: 'AddSupplierDialog',
  props: {
    projectId: {
      type: Number,
      required: true
    }
  },
  emits: ['close', 'success'],
  setup(props, { emit }) {
    const fileInput = ref(null)
    const selectedFile = ref(null)
    const submitting = ref(false)
    const submitError = ref('')
    
    const form = reactive({
      name: '',
      registrationNumber: ''
    })
    
    const errors = reactive({
      name: '',
      registrationNumber: '',
      file: ''
    })

    const validate = () => {
      let valid = true
      errors.name = ''
      errors.registrationNumber = ''
      errors.file = ''

      if (!form.name.trim()) {
        errors.name = '请输入供应商名称'
        valid = false
      }

      if (!form.registrationNumber.trim()) {
        errors.registrationNumber = '请输入社会信用代码'
        valid = false
      }

      if (selectedFile.value) {
        const ext = selectedFile.value.name.split('.').pop().toLowerCase()
        if (!['doc', 'docx'].includes(ext)) {
          errors.file = '投标文件必须是 .doc 或 .docx 格式'
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

    const triggerFileInput = () => {
      fileInput.value?.click()
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
        
        await createBidRecord(
          props.projectId,
          form.name.trim(),
          form.registrationNumber.trim(),
          selectedFile.value
        )
        
        emit('success')
      } catch (err) {
        submitError.value = err.message || '添加供应商失败'
      } finally {
        submitting.value = false
      }
    }

    return {
      fileInput,
      selectedFile,
      form,
      errors,
      submitting,
      submitError,
      handleFileChange,
      triggerFileInput,
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
</style>
