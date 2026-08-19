<template>
  <span class="status-badge" :class="[colorClass, size]">
    <svg class="status-icon" :width="iconSize" :height="iconSize" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <template v-if="iconShape === 'warning'">
        <path d="M8 1l7 13H1L8 1zm0 4v4m0 2h.01" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
      </template>
      <template v-else-if="iconShape === 'check'">
        <path d="M3 8.5l3.5 3.5L13 4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
      </template>
      <template v-else-if="iconShape === 'clock'">
        <circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.5" />
        <path d="M8 4.5v4l2.5 1.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
      </template>
      <template v-else-if="iconShape === 'arrow'">
        <path d="M8 3v10M4 7l4-4 4 4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
      </template>
      <template v-else-if="iconShape === 'x'">
        <path d="M4 4l8 8M12 4l-8 8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
      </template>
      <template v-else>
        <circle cx="8" cy="8" r="3" />
      </template>
    </svg>
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

const iconMap = {
  warning: 'clock',
  primary: 'arrow',
  accent: 'arrow',
  success: 'check',
  danger: 'x'
}

const dangerStatuses = ['critical', 'catastrophic', 'extreme']

const colorClass = computed(() => {
  const key = props.status?.toLowerCase().replace(/[\s-]/g, '_')
  return colorMap[key] || 'primary'
})

const iconShape = computed(() => {
  const key = props.status?.toLowerCase().replace(/[\s-]/g, '_')
  if (dangerStatuses.includes(key)) return 'warning'
  return iconMap[colorClass.value] || 'clock'
})

const iconSize = computed(() => props.size === 'sm' ? 10 : 12)

const displayLabel = computed(() => {
  return props.status?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || ''
})
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  border-radius: var(--radius, 10px);
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

.status-icon {
  flex-shrink: 0;
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
