<template>
  <div class="coordination">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <!-- Filters -->
    <div class="filters-bar">
      <div class="filter-group">
        <label class="filter-label">{{ $t('coordination.disaster') }}</label>
        <select v-model="selectedDisaster" class="filter-select">
          <option value="">{{ $t('coordination.allDisasters') }}</option>
          <option v-for="d in disasters" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">{{ $t('coordination.activity') }}</label>
        <select v-model="selectedActivity" class="filter-select">
          <option value="">{{ $t('coordination.allActivities') }}</option>
          <option v-for="a in activityTypes" :key="a" :value="a">{{ formatActivity(a) }}</option>
        </select>
      </div>
      <div class="filter-actions">
        <span class="entry-count">{{ filteredEntries.length }} {{ $t('coordination.entries') }}</span>
        <button class="btn-primary" @click="showModal = true">+ {{ $t('coordination.addActivity') }}</button>
      </div>
    </div>

    <!-- Map -->
    <div class="map-panel">
      <div class="panel-header">
        <h2 class="panel-title">{{ $t('coordination.activityMap') }}</h2>
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
        <h2 class="panel-title">{{ $t('coordination.matrix') }}</h2>
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
        <template #cell-actions="{ row }">
          <button class="btn-icon-danger" @click.stop="deleteEntry(row.id)" :title="$t('common.delete')">&#10005;</button>
        </template>
      </DataTable>
    </div>

    <!-- Loading / Error overlays -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <span>{{ $t('coordination.loadingData') }}</span>
    </div>
    <!-- Create Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="coord-modal-title" @keydown.escape="showModal = false">
        <div class="modal-header">
          <h3 id="coord-modal-title">{{ $t('coordination.add3WActivity') }}</h3>
          <button class="modal-close" @click="showModal = false" :aria-label="$t('common.close')">&times;</button>
        </div>
        <form @submit.prevent="createEntry" class="modal-body">
          <div class="form-group">
            <label for="coord-disaster">{{ $t('coordination.disaster') }}</label>
            <select id="coord-disaster" v-model="form.disaster_id" required>
              <option :value="null" disabled>{{ $t('coordination.selectDisaster') }}</option>
              <option v-for="d in disasters" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="coord-org">{{ $t('coordination.organization') }}</label>
              <input id="coord-org" v-model="form.organization_name" required :placeholder="$t('coordination.orgPlaceholder')" />
            </div>
            <div class="form-group">
              <label for="coord-activity">{{ $t('coordination.activityType') }}</label>
              <select id="coord-activity" v-model="form.activity" required>
                <option value="food_distribution">{{ $t('coordination.foodDistribution') }}</option>
                <option value="medical">{{ $t('coordination.medical') }}</option>
                <option value="shelter">{{ $t('coordination.shelter') }}</option>
                <option value="water">{{ $t('coordination.water') }}</option>
                <option value="logistics">{{ $t('coordination.logistics') }}</option>
                <option value="protection">{{ $t('coordination.protection') }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="coord-location">{{ $t('common.location') }}</label>
              <input id="coord-location" v-model="form.location" required :placeholder="$t('coordination.locationPlaceholder')" />
            </div>
            <div class="form-group">
              <label for="coord-beneficiaries">{{ $t('coordination.beneficiaries') }}</label>
              <input id="coord-beneficiaries" type="number" v-model.number="form.beneficiaries" :placeholder="$t('coordination.beneficiariesPlaceholder')" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="coord-lat">{{ $t('coordination.latitude') }}</label>
              <input id="coord-lat" type="number" step="any" v-model.number="form.latitude" :placeholder="$t('coordination.latPlaceholder')" />
            </div>
            <div class="form-group">
              <label for="coord-lng">{{ $t('coordination.longitude') }}</label>
              <input id="coord-lng" type="number" step="any" v-model.number="form.longitude" :placeholder="$t('coordination.lngPlaceholder')" />
            </div>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showModal = false">{{ $t('common.cancel') }}</button>
            <button type="submit" class="btn-primary" :disabled="creating">{{ creating ? $t('coordination.saving') : $t('coordination.addActivity') }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import MapView from '../components/common/MapView.vue'
import DataTable from '../components/common/DataTable.vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { coordinationApi, disastersApi } from '../api/client'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const loading = ref(true)
const entries = ref([])
const disasters = ref([])
const selectedDisaster = ref('')
const selectedActivity = ref('')
const showModal = ref(false)
const creating = ref(false)

const form = ref({
  disaster_id: null,
  organization_name: '',
  activity: 'food_distribution',
  location: '',
  beneficiaries: null,
  latitude: null,
  longitude: null
})

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
  { key: 'status', label: 'Status', sortable: true },
  { key: 'actions', label: '', width: '50px' }
]

function formatActivity(activity) {
  if (!activity) return '-'
  return activity.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

async function createEntry() {
  creating.value = true
  try {
    await coordinationApi.create(form.value)
    showModal.value = false
    form.value = { disaster_id: null, organization_name: '', activity: 'food_distribution', location: '', beneficiaries: null, latitude: null, longitude: null }
    await reload()
  } catch (e) {
    handleError(e, 'Failed to create entry')
  } finally {
    creating.value = false
  }
}

async function deleteEntry(id) {
  try {
    await coordinationApi.delete(id)
    entries.value = entries.value.filter(e => e.id !== id)
  } catch (e) {
    handleError(e, 'Failed to delete entry')
  }
}

async function reload() {
  loading.value = true
  try {
    const { data } = await coordinationApi.list()
    entries.value = Array.isArray(data) ? data : []
  } catch (e) {
    handleError(e, 'Failed to load coordination data')
  } finally {
    loading.value = false
  }
}

function retryLoad() {
  clearError()
  reload()
}

onMounted(async () => {
  const [, disasterRes] = await Promise.allSettled([
    reload(),
    disastersApi.list()
  ])
  if (disasterRes.status === 'fulfilled') {
    disasters.value = Array.isArray(disasterRes.value.data) ? disasterRes.value.data : []
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
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: 13px;
  min-width: 180px;
}

.filter-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.entry-count {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.map-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
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

.panel-header .panel-title {
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
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.table-panel .panel-header {
  border-bottom: none;
}

.activity-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--radius);
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

.status-dot.active::before { background: var(--success); }
.status-dot.planned::before { background: var(--warning); }
.status-dot.completed::before { background: var(--primary); }

.btn-primary {
  padding: 8px 16px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}
.btn-primary:hover { opacity: 0.9; }
.btn-primary:disabled { opacity: 0.5; cursor: default; }

.btn-secondary {
  padding: 8px 16px;
  background: var(--surface);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.btn-icon-danger {
  background: none;
  border: none;
  color: var(--danger);
  font-size: 14px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  opacity: 0.6;
  transition: opacity 0.15s;
}
.btn-icon-danger:hover { opacity: 1; }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  width: 90%;
  max-width: 540px;
  box-shadow: var(--shadow-lg, 0 8px 32px rgba(0,0,0,0.3));
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--text-secondary);
  cursor: pointer;
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 8px;
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
  border-radius: var(--radius);
  padding: 12px 20px;
  color: var(--danger);
  font-size: 14px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
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
  .filter-actions {
    margin-left: 0;
    justify-content: space-between;
  }
  .map-wrapper { height: 300px; }
  .form-row { flex-direction: column; }
}
</style>
