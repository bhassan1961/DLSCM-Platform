<template>
  <div class="stat-card" :style="borderStyle">
    <div class="stat-header">
      <span class="stat-icon">{{ icon }}</span>
      <span v-if="trend" class="stat-trend" :class="trendClass">{{ trend }}</span>
    </div>
    <div class="stat-value">{{ value }}</div>
    <div class="stat-label">{{ label }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  icon: { type: String, default: '' },
  trend: { type: String, default: '' },
  color: { type: String, default: 'var(--primary)' }
})

const borderStyle = computed(() => ({
  borderTop: `3px solid ${props.color}`
}))

const trendClass = computed(() => {
  if (!props.trend) return ''
  return props.trend.startsWith('+') ? 'positive' : props.trend.startsWith('-') ? 'negative' : ''
})
</script>

<style scoped>
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.stat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.stat-icon {
  font-size: 24px;
}

.stat-trend {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}

.stat-trend.positive {
  background: rgba(39, 174, 96, 0.12);
  color: var(--success);
}

.stat-trend.negative {
  background: rgba(231, 76, 60, 0.12);
  color: var(--danger);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}
</style>
