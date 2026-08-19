<template>
  <div class="stat-card" :class="{ clickable, active }" role="button" tabindex="0" @click="$emit('select')" @keydown.enter="$emit('select')">
    <div class="stat-accent" :style="{ background: color }"></div>
    <div class="stat-body">
      <div class="stat-header">
        <SvgIcon v-if="iconName" :name="iconName" :size="22" class="stat-icon" :style="{ color: color }" />
        <span v-else-if="icon" class="stat-icon-text" :style="{ color: color }">{{ icon }}</span>
        <span v-if="trend" class="stat-trend" :class="trendClass">{{ trend }}</span>
      </div>
      <div class="stat-value">{{ value }}</div>
      <div class="stat-label">{{ label }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import SvgIcon from './SvgIcon.vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  icon: { type: String, default: '' },
  iconName: { type: String, default: '' },
  trend: { type: String, default: '' },
  color: { type: String, default: 'var(--primary)' },
  clickable: { type: Boolean, default: false },
  active: { type: Boolean, default: false }
})

defineEmits(['select'])

const trendClass = computed(() => {
  if (!props.trend) return ''
  return props.trend.startsWith('+') ? 'positive' : props.trend.startsWith('-') ? 'negative' : ''
})
</script>

<style scoped>
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  display: flex;
  overflow: hidden;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.stat-card.clickable {
  cursor: pointer;
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.stat-card.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent), var(--shadow-md);
}

.stat-accent {
  width: 4px;
  flex-shrink: 0;
}

.stat-body {
  padding: 18px 20px;
  flex: 1;
  min-width: 0;
}

.stat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.stat-icon-text {
  font-size: 22px;
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
  font-size: 30px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}
</style>
