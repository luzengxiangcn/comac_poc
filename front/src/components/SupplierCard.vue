<template>
  <div class="supplier-card card">
    <div class="supplier-name">{{ getSupplierName() }}</div>
    <div class="supplier-tags" v-if="isIdentifying()">
      <span class="identifying-tag" v-for="n in 3" :key="n">识别中..</span>
    </div>
    <div class="supplier-info">
      <div class="info-item">
        <span class="label">社会信用代码：</span>
        <span class="value">{{ bidRecord.supplier?.registration_number || '识别中...' }}</span>
      </div>
      <div class="info-item" v-if="bidRecord.bid_file">
        <span class="label">投标文件：</span>
        <span class="value file-name">{{ bidRecord.bid_file.file_name }}</span>
      </div>
      <div class="info-item">
        <span class="label">初审状态：</span>
        <span :class="['status-badge', getPreliminaryStatusClass()]">
          {{ getPreliminaryStatusText() }}
        </span>
      </div>
      <div class="info-item">
        <span class="label">评审成功：</span>
        <span :class="['status-badge', getEvaluationStatusClass()]">
          {{ getEvaluationStatusText() }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SupplierCard',
  props: {
    bidRecord: {
      type: Object,
      required: true
    }
  },
  methods: {
    getSupplierName() {
      const name = this.bidRecord.supplier?.name
      if (!name || name === '未知供应商') {
        return '未知供应商'
      }
      return name
    },
    isIdentifying() {
      // 如果 identity_recognition_model_session 存在且 identity_status 为 "识别中"
      return this.bidRecord.identity_recognition_model_session && 
             this.bidRecord.identity_status === '识别中'
    },
    getPreliminaryStatusText() {
      const status = this.bidRecord.ai_preliminary_review_success
      if (status === true) {
        return '通过'
      } else if (status === false) {
        return '不通过'
      } else {
        // null 或 undefined
        return '未开始'
      }
    },
    getPreliminaryStatusClass() {
      const status = this.bidRecord.ai_preliminary_review_success
      if (status === true) {
        return 'status-success'
      } else if (status === false) {
        return 'status-failed'
      } else {
        // null 或 undefined
        return 'status-pending'
      }
    },
    getEvaluationStatusText() {
      const status = this.bidRecord.ai_evaluation_success
      if (status === true) {
        return '是'
      } else if (status === false) {
        return '否'
      } else {
        // null 或 undefined
        return '未评审'
      }
    },
    getEvaluationStatusClass() {
      const status = this.bidRecord.ai_evaluation_success
      if (status === true) {
        return 'status-success'
      } else if (status === false) {
        return 'status-failed'
      } else {
        // null 或 undefined
        return 'status-pending'
      }
    }
  }
}
</script>

<style scoped>
.supplier-card {
  padding: 20px;
  min-height: 150px;
}

.supplier-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
  word-break: break-word;
}

.supplier-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.identifying-tag {
  display: inline-block;
  padding: 4px 8px;
  background-color: #e3f2fd;
  color: #1976d2;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.supplier-info {
  margin-top: 12px;
}

.info-item {
  font-size: 13px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.label {
  color: var(--text-secondary);
  flex-shrink: 0;
  margin-right: 8px;
}

.value {
  color: var(--text-primary);
  word-break: break-word;
  text-align: right;
  flex: 1;
}

.file-name {
  color: var(--primary-color);
  cursor: pointer;
}

.file-name:hover {
  text-decoration: underline;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-success {
  background-color: #d4edda;
  color: #155724;
}

.status-failed {
  background-color: #f8d7da;
  color: #721c24;
}

.status-pending {
  background-color: #fff3cd;
  color: #856404;
}
</style>
