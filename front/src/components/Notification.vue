<template>
  <Transition name="notification">
    <div v-if="visible" class="notification" :class="type">
      <div class="notification-content">
        <span class="notification-message">{{ message }}</span>
        <button class="notification-close" @click="close">×</button>
      </div>
    </div>
  </Transition>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'Notification',
  props: {
    message: {
      type: String,
      required: true
    },
    type: {
      type: String,
      default: 'success',
      validator: (value) => ['success', 'error', 'info', 'warning'].includes(value)
    },
    duration: {
      type: Number,
      default: 3000
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const visible = ref(false)

    const close = () => {
      visible.value = false
      setTimeout(() => {
        emit('close')
      }, 300) // 等待动画完成
    }

    onMounted(() => {
      visible.value = true
      if (props.duration > 0) {
        setTimeout(() => {
          close()
        }, props.duration)
      }
    })

    return {
      visible,
      close
    }
  }
}
</script>

<style scoped>
.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  min-width: 300px;
  max-width: 400px;
  padding: 16px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  background-color: white;
  border-left: 4px solid;
}

.notification.success {
  border-left-color: #52c41a;
}

.notification.error {
  border-left-color: #ff4d4f;
}

.notification.info {
  border-left-color: #1890ff;
}

.notification.warning {
  border-left-color: #faad14;
}

.notification-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.notification-message {
  flex: 1;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.5;
}

.notification-close {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s;
  flex-shrink: 0;
}

.notification-close:hover {
  color: var(--text-primary);
}

.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>

