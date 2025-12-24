<template>
  <div
    class="supplier-card card"
    :class="{ clickable: clickable, selected: selected }"
    @click="handleClick"
  >
    <div class="supplier-name">{{ getSupplierName() }}</div>
    <div class="supplier-tags" v-if="isIdentifying()">
      <span class="identifying-tag">识别中..</span>
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
        <span :class="['status-badge', getPreliminaryStatusClass(), { 'ai-review-badge': isPreliminaryFromAI() }]">
          {{ getPreliminaryStatusText() }}
        </span>
      </div>
      <div class="info-item">
        <span class="label">标书评审：</span>
        <span :class="['status-badge', getEvaluationStatusClass()]">
          {{ getEvaluationStatusText() }}
        </span>
      </div>
      <div class="info-item ai-preliminary-review-item" @click.stop="handleAiPreliminaryClick">
        <span class="label">AI初评：</span>
        <span :class="['status-badge', getAiPreliminaryStatusClass()]">
          {{ getAiPreliminaryStatusText() }}
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
    },
    // 是否可点击用于选择
    clickable: {
      type: Boolean,
      default: false
    },
    // 是否为当前选中卡片
    selected: {
      type: Boolean,
      default: false
    }
  },
  emits: ['select', 'ai-preliminary-click'],
  methods: {
    handleClick() {
      if (this.clickable) {
        this.$emit('select', this.bidRecord)
      }
    },
    handleAiPreliminaryClick() {
      const status = this.getAiPreliminaryStatus()
      // 只有运行中和成功状态可以点击
      if (status === 'running' || status === 'success') {
        this.$emit('ai-preliminary-click', this.bidRecord)
      }
    },
    getAiPreliminaryStatus() {
      // 优先使用后端返回的状态字段（如果存在）
      if (this.bidRecord.ai_preliminary_status) {
        const status = this.bidRecord.ai_preliminary_status
        if (status === '运行中') {
          return 'running'
        } else if (status === '已完成') {
          return 'success'
        } else if (status === '失败') {
          return 'failed'
        }
      }
      // 如果有 model_session，说明正在进行中
      if (this.bidRecord.ai_preliminary_review_model_session) {
        return 'running'
      }
      // 如果没有 model_session，但有 ai_preliminary_review，说明已成功
      if (this.bidRecord.ai_preliminary_review) {
        return 'success'
      }
      // 否则是未开始
      return 'not_started'
    },
    getAiPreliminaryStatusText() {
      const status = this.getAiPreliminaryStatus()
      if (status === 'running') {
        return '运行中'
      } else if (status === 'success') {
        return '成功'
      } else if (status === 'failed') {
        return '失败'
      }
      return '未开始'
    },
    getAiPreliminaryStatusClass() {
      const status = this.getAiPreliminaryStatus()
      if (status === 'running') {
        return 'status-running'
      } else if (status === 'success') {
        return 'status-finished'
      } else if (status === 'failed') {
        return 'status-failed'
      }
      return 'status-pending'
    },
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
      // 优先显示人工初审结果（preliminary_review.pass）
      const preliminaryReview = this.bidRecord.preliminary_review
      if (preliminaryReview) {
        // 如果是字符串，尝试解析
        let reviewData = preliminaryReview
        if (typeof preliminaryReview === 'string') {
          try {
            reviewData = JSON.parse(preliminaryReview)
          } catch (e) {
            console.error('解析人工初审JSON失败:', e, preliminaryReview)
            return '未开始'
          }
        }
        
        // 检查 pass 字段
        if (reviewData && (reviewData.pass === true || reviewData.pass === false)) {
          return reviewData.pass === true ? '通过' : '不通过'
        }
      }
      
      // 如果没有人工初审，显示AI初审结果（ai_preliminary_review.pass）
      const aiReview = this.bidRecord.ai_preliminary_review
      if (aiReview) {
        // 如果是字符串，尝试解析
        let reviewData = aiReview
        if (typeof aiReview === 'string') {
          try {
            reviewData = JSON.parse(aiReview)
          } catch (e) {
            console.error('解析AI初审JSON失败:', e, aiReview)
            return '未开始'
          }
        }
        
        // 检查 pass 字段（支持布尔值和字符串）
        if (reviewData) {
          const passValue = reviewData.pass
          if (passValue === true || passValue === 'true' || passValue === 'True') {
            return '通过'
          } else if (passValue === false || passValue === 'false' || passValue === 'False') {
            return '不通过'
          }
        }
      }
      
      return '未开始'
    },
    getPreliminaryStatusClass() {
      // 优先显示人工初审结果（preliminary_review.pass）
      const preliminaryReview = this.bidRecord.preliminary_review
      if (preliminaryReview) {
        // 如果是字符串，尝试解析
        let reviewData = preliminaryReview
        if (typeof preliminaryReview === 'string') {
          try {
            reviewData = JSON.parse(preliminaryReview)
          } catch (e) {
            return 'status-pending'
          }
        }
        
        // 检查 pass 字段
        if (reviewData && (reviewData.pass === true || reviewData.pass === false)) {
          return reviewData.pass === true ? 'status-success' : 'status-failed'
        }
      }
      
      // 如果没有人工初审，显示AI初审结果（ai_preliminary_review.pass）
      const aiReview = this.bidRecord.ai_preliminary_review
      if (aiReview) {
        // 如果是字符串，尝试解析
        let reviewData = aiReview
        if (typeof aiReview === 'string') {
          try {
            reviewData = JSON.parse(aiReview)
          } catch (e) {
            return 'status-pending'
          }
        }
        
        // 检查 pass 字段（支持布尔值和字符串）
        if (reviewData) {
          const passValue = reviewData.pass
          if (passValue === true || passValue === 'true' || passValue === 'True') {
            return 'status-success'
          } else if (passValue === false || passValue === 'false' || passValue === 'False') {
            return 'status-failed'
          }
        }
      }
      
      return 'status-pending'
    },
    isPreliminaryFromAI() {
      // 判断当前显示的初审结果是否来自AI
      const preliminaryReview = this.bidRecord.preliminary_review
      if (preliminaryReview) {
        // 如果有人工初审结果，返回false
        let reviewData = preliminaryReview
        if (typeof preliminaryReview === 'string') {
          try {
            reviewData = JSON.parse(preliminaryReview)
          } catch (e) {
            return false
          }
        }
        if (reviewData && typeof reviewData.pass !== 'undefined') {
          return false // 有人工初审，不是AI
        }
      }
      
      // 如果没有人工初审，但有AI初审，返回true
      const aiReview = this.bidRecord.ai_preliminary_review
      if (aiReview) {
        let reviewData = aiReview
        if (typeof aiReview === 'string') {
          try {
            reviewData = JSON.parse(aiReview)
          } catch (e) {
            return false
          }
        }
        if (reviewData && typeof reviewData.pass !== 'undefined') {
          return true // 是AI初审结果
        }
      }
      
      return false
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

.supplier-card.clickable {
  cursor: pointer;
  transition: box-shadow 0.2s ease, border-color 0.2s ease, transform 0.1s ease;
}

.supplier-card.clickable:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: var(--primary-color);
  transform: translateY(-2px);
}

.supplier-card.selected {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.ai-preliminary-review-item {
  cursor: pointer;
  transition: background-color 0.2s;
}

.ai-preliminary-review-item:hover {
  background-color: #f5f5f5;
  border-radius: 4px;
  padding: 4px 8px;
  margin: 4px -8px;
}

.status-running {
  background-color: #e3f2fd;
  color: #1976d2;
}

.status-finished {
  background-color: #d4edda;
  color: #155724;
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

/* AI评审结果样式 - 颜色更淡 */
.ai-review-badge.status-success {
  background-color: #d1e7dd;
  color: #0f5132;
  opacity: 0.75;
}

.ai-review-badge.status-failed {
  background-color: #f1aeb5;
  color: #58151c;
  opacity: 0.75;
}

.ai-review-badge.status-pending {
  background-color: #ffeaa7;
  color: #856404;
  opacity: 0.75;
}
</style>
