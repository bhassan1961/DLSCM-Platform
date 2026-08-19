<template>
  <div v-if="error" class="error-banner" role="alert">
    <div class="error-content">
      <svg class="error-icon" viewBox="0 0 20 20" fill="currentColor" width="20" height="20">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd"/>
      </svg>
      <span class="error-text">{{ error }}</span>
    </div>
    <div class="error-actions">
      <button v-if="onRetry" class="retry-btn" @click="onRetry">
        {{ $t('common.retry') }}
      </button>
      <button class="dismiss-btn" @click="$emit('dismiss')" :aria-label="$t('common.close')">
        &times;
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  error: { type: String, default: null },
  onRetry: { type: Function, default: null },
})
defineEmits(['dismiss'])
</script>

<style scoped>
.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
  background: var(--danger-bg, rgba(239, 68, 68, 0.08));
  border: 1px solid var(--danger, #ef4444);
  border-radius: var(--radius, 8px);
  color: var(--danger, #ef4444);
  font-size: 14px;
  animation: slideDown 0.2s ease;
}

.error-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.error-icon { flex-shrink: 0; }

.error-text {
  overflow: hidden;
  text-overflow: ellipsis;
}

.error-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.retry-btn {
  padding: 4px 14px;
  border: 1px solid var(--danger, #ef4444);
  border-radius: var(--radius-sm, 6px);
  background: transparent;
  color: var(--danger, #ef4444);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.retry-btn:hover {
  background: var(--danger, #ef4444);
  color: #fff;
}

.dismiss-btn {
  background: none;
  border: none;
  color: var(--danger, #ef4444);
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  padding: 0 4px;
  opacity: 0.7;
}

.dismiss-btn:hover { opacity: 1; }

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
