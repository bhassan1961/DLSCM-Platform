<template>
  <span class="status-badge" :class="[colorClass, size]">
    {{ displayLabel }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, required: true },
  size: { type: String, default: 'md', validator: v => ['sm', 'md'].includes(v) }
})

const colorMap = {
  pending: 'warning',
  monitoring: 'warning',
  approved: 'primary',
  active: 'primary',
  dispatched: 'accent',
  in_transit: 'accent',
  response: 'accent',
  sourcing: 'accent',
  delivered: 'success',
  completed: 'success',
  closed: 'success',
  fulfilled: 'success',
  cancelled: 'danger',
  failed: 'danger',
  critical: 'danger',
  catastrophic: 'danger',
  extreme: 'danger',
  high: 'warning',
  severe: 'warning',
  major: 'warning',
  medium: 'primary',
  moderate: 'primary',
  low: 'success',
  minor: 'success'
}

const colorClass = computed(() => {
  const key = props.status?.toLowerCase().replace(/[\s-]/g, '_')
  return colorMap[key] || 'primary'
})

const displayLabel = computed(() => {
  return props.status?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || ''
})
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  font-weight: 600;
  border-radius: 12px;
  white-space: nowrap;
  text-transform: capitalize;
}

.status-badge.md {
  font-size: 12px;
  padding: 4px 12px;
}

.status-badge.sm {
  font-size: 10px;
  padding: 2px 8px;
}

.status-badge.warning {
  background: rgba(243, 156, 18, 0.12);
  color: var(--warning);
}

.status-badge.primary {
  background: rgba(30, 58, 95, 0.12);
  color: var(--primary);
}

.status-badge.accent {
  background: rgba(232, 145, 58, 0.12);
  color: var(--accent);
}

.status-badge.success {
  background: rgba(39, 174, 96, 0.12);
  color: var(--success);
}

.status-badge.danger {
  background: rgba(231, 76, 60, 0.12);
  color: var(--danger);
}
</style>
