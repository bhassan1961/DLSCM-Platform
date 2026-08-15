<template>
  <div class="coordination">
    <!-- Filters -->
    <div class="filters-bar">
      <div class="filter-group">
        <label class="filter-label">Disaster</label>
        <select v-model="selectedDisaster" class="filter-select">
          <option value="">All Disasters</option>
          <option v-for="d in disasters" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">Activity</label>
        <select v-model="selectedActivity" class="filter-select">
          <option value="">All Activities</option>
          <option v-for="a in activityTypes" :key="a" :value="a">{{ formatActivity(a) }}</option>
        </select>
      </div>
      <div class="filter-summary">
        <span class="entry-count">{{ filteredEntries.length }} entries</span>
      </div>
    </div>

    <!-- Map -->
    <div class="map-panel">
      <div class="panel-header">
        <h3>3W Activity Map</h3>
        <div class="legend">
          <span class="legend-item" v-for="(color, activity) in activityColors" :key="activity">
            <span class="legend-dot" :style="{ background: color }"></span>
            {{ formatActivity(activity) }}
          </span>
        </div>
      </div>
      <div class="map-wrapper">
        <MapView
          :markers="mapMarkers"
          :center="[3.5, 36]"
          :zoom="5"
        />
      </div>
    </div>

    <!-- Data Table -->
    <div class="table-panel">
      <div class="panel-header">
        <h3>Coordination Matrix</h3>
      </div>
      <DataTable
        :columns="columns"
        :rows="filteredEntries"
        :loading="loading"
      >
        <template #cell-activity="{ value }">
          <span class="activity-badge" :style="{ background: activityColors[value] || '#888', color: '#fff' }">
            {{ formatActivity(value) }}
          </span>
        </template>
        <template #cell-beneficiaries="{ value }">
          {{ value != null ? value.toLocaleString() : '-' }}
        </template>
        <template #cell-status="{ value }">
          <span class="status-dot" :class="value">{{ value }}</span>
        </template>
      </DataTable>
    </div>

    <!-- Loading / Error overlays -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <span>Loading coordination data...</span>
    </div>
    <div v-if="error" class="error-banner">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import MapView from '../components/common/MapView.vue'
import DataTable from '../components/common/DataTable.vue'
import { coordinationApi, disastersApi } from '../api/client'

const loading = ref(true)
const error = ref(null)
const entries = ref([])
const disasters = ref([])
const selectedDisaster = ref('')
const selectedActivity = ref('')

const activityColors = {
  food_distribution: '#27ae60',
  medical: '#e74c3c',
  shelter: '#3498db',
  water: '#00bcd4',
  logistics: '#e8913a',
  protection: '#8e44ad'
}

const activityTypes = computed(() => {
  const types = new Set(entries.value.map(e => e.activity).filter(Boolean))
  return [...types].sort()
})

const filteredEntries = computed(() => {
  let result = entries.value
  if (selectedDisaster.value) {
    result = result.filter(e => e.disaster_id === selectedDisaster.value)
  }
  if (selectedActivity.value) {
    result = result.filter(e => e.activity === selectedActivity.value)
  }
  return result
})

const mapMarkers = computed(() => {
  return filteredEntries.value
    .filter(e => e.latitude != null && e.longitude != null)
    .map(e => ({
      lat: e.latitude,
      lng: e.longitude,
      color: activityColors[e.activity] || '#888',
      radius: Math.max(6, Math.min(14, Math.sqrt((e.beneficiaries || 1000) / 500))),
      popup: `<strong>${e.organization_name}</strong><br>${formatActivity(e.activity)}<br>${e.location}<br>${(e.beneficiaries || 0).toLocaleString()} beneficiaries`
    }))
})

const columns = [
  { key: 'organization_name', label: 'Organization', sortable: true },
  { key: 'activity', label: 'Activity', sortable: true },
  { key: 'location', label: 'Location', sortable: true },
  { key: 'beneficiaries', label: 'Beneficiaries', sortable: true },
  { key: 'status', label: 'Status', sortable: true }
]

function formatActivity(activity) {
  if (!activity) return '-'
  return activity.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

onMounted(async () => {
  try {
    const [coordRes, disasterRes] = await Promise.allSettled([
      coordinationApi.list(),
      disastersApi.list()
    ])
    if (coordRes.status === 'fulfilled') {
      const raw = coordRes.value.data
      entries.value = Array.isArray(raw) ? raw : []
    }
    if (disasterRes.status === 'fulfilled') {
      const raw = disasterRes.value.data
      disasters.value = Array.isArray(raw) ? raw : []
    }
  } catch (e) {
    error.value = 'Failed to load coordination data. Please try again.'
    console.error('Coordination load error:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.coordination {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.filters-bar {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--text);
  font-size: 13px;
  min-width: 180px;
}

.filter-summary {
  margin-left: auto;
  display: flex;
  align-items: center;
}

.entry-count {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.map-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
  gap: 8px;
}

.panel-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.legend {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-secondary);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.map-wrapper {
  height: 400px;
}

.table-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.table-panel .panel-header {
  border-bottom: none;
}

.activity-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 10px;
  white-space: nowrap;
}

.status-dot {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  text-transform: capitalize;
}

.status-dot::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-secondary);
}

.status-dot.active::before {
  background: var(--success);
}

.status-dot.planned::before {
  background: var(--warning);
}

.status-dot.completed::before {
  background: var(--primary);
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px;
  color: var(--text-secondary);
  font-size: 14px;
}

.error-banner {
  background: rgba(231, 76, 60, 0.1);
  border: 1px solid var(--danger);
  border-radius: 8px;
  padding: 12px 20px;
  color: var(--danger);
  font-size: 14px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .filters-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-summary {
    margin-left: 0;
  }

  .map-wrapper {
    height: 300px;
  }
}
</style>
