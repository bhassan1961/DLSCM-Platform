<template>
  <div class="resilience">
    <div class="page-header">
      <h2>Community Toolkit</h2>
      <p class="page-subtitle">Disaster preparedness checklists for communities</p>
    </div>

    <!-- Overall Progress -->
    <div class="progress-card">
      <div class="progress-header">
        <span class="progress-label">Overall Preparedness</span>
        <span class="progress-pct">{{ overallPct }}%</span>
      </div>
      <div class="progress-track">
        <div
          class="progress-fill"
          :style="{ width: overallPct + '%', background: progressColor(overallPct) }"
        ></div>
      </div>
      <p class="progress-summary">{{ totalChecked }} of {{ totalItems }} items complete</p>
    </div>

    <!-- Sections -->
    <div class="sections">
      <div v-for="section in sections" :key="section.key" class="section-card">
        <div class="section-header">
          <div class="section-title-row">
            <span class="section-icon">{{ section.icon }}</span>
            <h3 class="section-title">{{ section.title }}</h3>
          </div>
          <span class="section-progress" :class="{ complete: sectionComplete(section) }">
            {{ sectionCheckedCount(section) }}/{{ section.items.length }} complete
          </span>
        </div>
        <div class="checklist">
          <label
            v-for="item in section.items"
            :key="item.id"
            class="check-item"
            :class="{ checked: checklist[item.id] }"
          >
            <input
              type="checkbox"
              :checked="checklist[item.id]"
              @change="toggleItem(item.id)"
            />
            <span class="check-box">
              <span v-if="checklist[item.id]" class="check-mark">&#10003;</span>
            </span>
            <span class="check-label">{{ item.label }}</span>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const STORAGE_KEY = 'dlscm-resilience-checklist'

const sections = [
  {
    key: 'contacts',
    title: 'Emergency Contacts',
    icon: '☎',
    items: [
      { id: 'contacts-1', label: 'Local emergency number' },
      { id: 'contacts-2', label: 'Hospital / clinic' },
      { id: 'contacts-3', label: 'Police' },
      { id: 'contacts-4', label: 'Fire service' },
      { id: 'contacts-5', label: 'Community leader' }
    ]
  },
  {
    key: 'evacuation',
    title: 'Evacuation Plan',
    icon: '\u{1F6A8}',
    items: [
      { id: 'evac-1', label: 'Identified routes' },
      { id: 'evac-2', label: 'Meeting point' },
      { id: 'evac-3', label: 'Transportation plan' },
      { id: 'evac-4', label: 'Practice drill completed' }
    ]
  },
  {
    key: 'supplies',
    title: 'Supply Inventory',
    icon: '\u{1F4E6}',
    items: [
      { id: 'supply-1', label: 'Water (3 days)' },
      { id: 'supply-2', label: 'Non-perishable food' },
      { id: 'supply-3', label: 'First aid kit' },
      { id: 'supply-4', label: 'Flashlight / batteries' },
      { id: 'supply-5', label: 'Important documents copied' },
      { id: 'supply-6', label: 'Cash reserve' }
    ]
  },
  {
    key: 'communication',
    title: 'Communication Plan',
    icon: '\u{1F4E1}',
    items: [
      { id: 'comm-1', label: 'Family contact list' },
      { id: 'comm-2', label: 'Out-of-area contact' },
      { id: 'comm-3', label: 'Radio / phone charging' },
      { id: 'comm-4', label: 'Social media plan' }
    ]
  },
  {
    key: 'firstaid',
    title: 'First Aid Knowledge',
    icon: '⚕',
    items: [
      { id: 'aid-1', label: 'CPR training' },
      { id: 'aid-2', label: 'Wound care basics' },
      { id: 'aid-3', label: 'Emergency signaling' }
    ]
  }
]

function loadChecklist() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved ? JSON.parse(saved) : {}
  } catch {
    return {}
  }
}

const checklist = ref(loadChecklist())

function saveChecklist() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(checklist.value))
  } catch {
    // localStorage may be unavailable
  }
}

function toggleItem(id) {
  checklist.value[id] = !checklist.value[id]
  saveChecklist()
}

const totalItems = computed(() => {
  return sections.reduce((sum, s) => sum + s.items.length, 0)
})

const totalChecked = computed(() => {
  return Object.values(checklist.value).filter(Boolean).length
})

const overallPct = computed(() => {
  if (totalItems.value === 0) return 0
  return Math.round((totalChecked.value / totalItems.value) * 100)
})

function sectionCheckedCount(section) {
  return section.items.filter(item => checklist.value[item.id]).length
}

function sectionComplete(section) {
  return sectionCheckedCount(section) === section.items.length
}

function progressColor(pct) {
  if (pct >= 80) return 'var(--success)'
  if (pct >= 40) return 'var(--warning)'
  return 'var(--accent)'
}

watch(checklist, saveChecklist, { deep: true })
</script>

<style scoped>
.resilience {
  max-width: 800px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

/* Progress card */
.progress-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.progress-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.progress-pct {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent);
}

.progress-track {
  height: 10px;
  background: var(--bg);
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.4s ease;
}

.progress-summary {
  font-size: 13px;
  color: var(--text-secondary);
}

/* Sections */
.sections {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.section-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-icon {
  font-size: 18px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.section-progress {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 3px 10px;
  border-radius: 10px;
  background: var(--bg);
}

.section-progress.complete {
  background: rgba(39, 174, 96, 0.12);
  color: var(--success);
}

/* Checklist */
.checklist {
  padding: 8px 12px;
}

.check-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.1s ease;
}

.check-item:hover {
  background: var(--bg);
}

.check-item input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.check-box {
  width: 22px;
  height: 22px;
  border: 2px solid var(--border);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s ease;
}

.check-item.checked .check-box {
  background: var(--success);
  border-color: var(--success);
}

.check-mark {
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  line-height: 1;
}

.check-label {
  font-size: 14px;
  color: var(--text);
  transition: opacity 0.15s ease;
}

.check-item.checked .check-label {
  opacity: 0.6;
  text-decoration: line-through;
}
</style>
