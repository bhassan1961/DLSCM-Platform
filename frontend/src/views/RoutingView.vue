<template>
  <div class="routing">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <!-- Controls Panel -->
    <div class="controls-panel">
      <div class="panel-header">
        <h2 class="panel-title">{{ $t('routing.routeParameters') }}</h2>
      </div>
      <div class="controls-body">
        <div class="control-row">
          <div class="control-group">
            <label class="control-label">{{ $t('routing.originWarehouse') }}</label>
            <select v-model="selectedWarehouse" class="control-select">
              <option :value="null" disabled>{{ $t('routing.selectWarehouse') }}</option>
              <option v-for="w in warehouses" :key="w.id" :value="w">
                {{ w.name }} ({{ w.location }})
              </option>
            </select>
          </div>
          <div class="control-group">
            <label class="control-label">{{ $t('routing.destinationDisaster') }}</label>
            <select v-model="selectedDisaster" class="control-select">
              <option :value="null" disabled>{{ $t('routing.selectDestination') }}</option>
              <option v-for="d in disasters" :key="d.id" :value="d">
                {{ d.name }}
              </option>
            </select>
          </div>
        </div>

        <div class="control-row">
          <div class="control-group">
            <label class="control-label">{{ $t('routing.transportMode') }}</label>
            <div class="mode-buttons">
              <label
                v-for="m in modes"
                :key="m.value"
                class="mode-btn"
                :class="{ active: selectedMode === m.value }"
              >
                <input
                  type="radio"
                  :value="m.value"
                  v-model="selectedMode"
                  class="mode-radio"
                />
                <SvgIcon :name="m.iconName" :size="16" class="mode-icon" />
                <span class="mode-label">{{ m.label }}</span>
              </label>
            </div>
          </div>
          <div class="control-group action-group">
            <button
              class="optimize-btn"
              :disabled="!canOptimize || loading"
              @click="optimize"
            >
              <span v-if="loading" class="btn-spinner"></span>
              {{ loading ? $t('routing.optimizing') : $t('routing.optimizeRoute') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Results -->
    <div class="results-layout" v-if="result || selectedWarehouse || selectedDisaster">
      <!-- Map -->
      <div class="map-panel">
        <div class="panel-header">
          <h2 class="panel-title">{{ $t('routing.routeMap') }}</h2>
        </div>
        <div class="map-wrapper">
          <MapView
            :markers="mapMarkers"
            :polylines="mapPolylines"
            :center="mapCenter"
            :zoom="mapZoom"
          />
        </div>
      </div>

      <!-- Route Details -->
      <div class="details-panel" v-if="result">
        <div class="panel-header">
          <h2 class="panel-title">{{ $t('routing.routeSummary') }}</h2>
        </div>
        <div class="details-body">
          <div class="detail-stat">
            <svg class="stat-icon-svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" /><polyline points="3.29 7 12 12 20.71 7" /><line x1="12" y1="22" x2="12" y2="12" /></svg>
            <div class="stat-info">
              <div class="stat-value">{{ result.total_distance_km?.toFixed(1) }} km</div>
              <div class="stat-label">{{ $t('routing.totalDistance') }}</div>
            </div>
          </div>
          <div class="detail-stat">
            <svg class="stat-icon-svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
            <div class="stat-info">
              <div class="stat-value">{{ formatDuration(result.total_duration_hours) }}</div>
              <div class="stat-label">{{ $t('routing.estimatedDuration') }}</div>
            </div>
          </div>
          <div class="detail-stat">
            <SvgIcon :name="modeIconName" :size="20" class="stat-icon-svg" />
            <div class="stat-info">
              <div class="stat-value">{{ formatMode(result.mode) }}</div>
              <div class="stat-label">{{ $t('routing.transportMode') }}</div>
            </div>
          </div>

          <!-- Legs -->
          <div class="legs-section" v-if="result.legs?.length">
            <h4>{{ $t('routing.routeLegs') }}</h4>
            <div
              v-for="(leg, idx) in result.legs"
              :key="idx"
              class="leg-card"
            >
              <div class="leg-header">
                <span class="leg-number">{{ $t('routing.leg') }} {{ idx + 1 }}</span>
                <span class="leg-mode">{{ formatMode(leg.mode) }}</span>
              </div>
              <div class="leg-details">
                <span>{{ leg.distance_km?.toFixed(1) }} km</span>
                <span class="leg-divider">|</span>
                <span>{{ formatDuration(leg.duration_hours) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!result && !selectedWarehouse && !selectedDisaster && !loading" class="empty-state">
      <svg class="empty-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="6" cy="19" r="3" /><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15" /><circle cx="18" cy="5" r="3" /></svg>
      <h2 class="empty-title">{{ $t('routing.emptyTitle') }}</h2>
      <p>{{ $t('routing.emptyDesc') }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import MapView from '../components/common/MapView.vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import SvgIcon from '../components/common/SvgIcon.vue'
import { inventoryApi, disastersApi, routingApi } from '../api/client'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const warehouses = ref([])
const disasters = ref([])
const selectedWarehouse = ref(null)
const selectedDisaster = ref(null)
const selectedMode = ref('road')
const loading = ref(false)
const result = ref(null)

const modes = [
  { value: 'road', label: 'Road', iconName: 'shipments' },
  { value: 'air', label: 'Air', iconName: 'forecast' },
  { value: 'sea', label: 'Sea', iconName: 'cross-org' }
]

const canOptimize = computed(() => {
  return selectedWarehouse.value && selectedDisaster.value
})

const modeIconName = computed(() => {
  const m = modes.find(m => m.value === result.value?.mode)
  return m?.iconName || 'shipments'
})

const mapMarkers = computed(() => {
  const markers = []
  if (selectedWarehouse.value?.latitude && selectedWarehouse.value?.longitude) {
    markers.push({
      lat: selectedWarehouse.value.latitude,
      lng: selectedWarehouse.value.longitude,
      color: '#3498db',
      radius: 10,
      popup: `<strong>Origin:</strong> ${selectedWarehouse.value.name}`
    })
  }
  if (selectedDisaster.value?.latitude && selectedDisaster.value?.longitude) {
    markers.push({
      lat: selectedDisaster.value.latitude,
      lng: selectedDisaster.value.longitude,
      color: '#e74c3c',
      radius: 10,
      popup: `<strong>Destination:</strong> ${selectedDisaster.value.name}`
    })
  }
  return markers
})

const mapPolylines = computed(() => {
  if (!result.value?.legs?.length) return []
  return result.value.legs.map(leg => ({
    points: [
      [leg.from.lat, leg.from.lng],
      [leg.to.lat, leg.to.lng]
    ],
    color: selectedMode.value === 'air' ? '#3498db' : selectedMode.value === 'sea' ? '#1abc9c' : '#e8913a'
  }))
})

const mapCenter = computed(() => {
  if (selectedWarehouse.value?.latitude && selectedDisaster.value?.latitude) {
    return [
      (selectedWarehouse.value.latitude + selectedDisaster.value.latitude) / 2,
      (selectedWarehouse.value.longitude + selectedDisaster.value.longitude) / 2
    ]
  }
  if (selectedWarehouse.value?.latitude) {
    return [selectedWarehouse.value.latitude, selectedWarehouse.value.longitude]
  }
  if (selectedDisaster.value?.latitude) {
    return [selectedDisaster.value.latitude, selectedDisaster.value.longitude]
  }
  return [5, 38]
})

const mapZoom = computed(() => {
  if (selectedWarehouse.value && selectedDisaster.value) return 5
  return 6
})

function formatDuration(hours) {
  if (hours == null) return '-'
  if (hours < 1) return `${Math.round(hours * 60)} min`
  const h = Math.floor(hours)
  const m = Math.round((hours - h) * 60)
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

function formatMode(mode) {
  if (!mode) return '-'
  return mode.charAt(0).toUpperCase() + mode.slice(1)
}

async function optimize() {
  if (!canOptimize.value) return
  loading.value = true
  clearError()
  result.value = null
  try {
    const payload = {
      origin: {
        lat: selectedWarehouse.value.latitude,
        lng: selectedWarehouse.value.longitude
      },
      destination: {
        lat: selectedDisaster.value.latitude,
        lng: selectedDisaster.value.longitude
      },
      mode: selectedMode.value
    }
    const { data } = await routingApi.optimize(payload)
    result.value = data
  } catch (e) {
    handleError(e, 'Failed to optimize route. Please try again.')
  } finally {
    loading.value = false
  }
}

async function loadData() {
  try {
    const [whRes, dRes] = await Promise.allSettled([
      inventoryApi.warehouses(),
      disastersApi.list()
    ])
    if (whRes.status === 'fulfilled') {
      warehouses.value = whRes.value.data?.warehouses || whRes.value.data || []
    }
    if (dRes.status === 'fulfilled') {
      disasters.value = dRes.value.data?.disasters || dRes.value.data || []
    }
  } catch (e) {
    handleError(e, 'Failed to load data')
  }
}

function retryLoad() {
  clearError()
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.routing {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.controls-panel {
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
}

.panel-header .panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.controls-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-row {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-width: 200px;
}

.action-group {
  flex: 0 0 auto;
  justify-content: flex-end;
}

.control-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
}

.control-select {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: 13px;
  width: 100%;
}

.mode-buttons {
  display: flex;
  gap: 8px;
}

.mode-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.mode-btn:hover {
  border-color: var(--primary);
  color: var(--text);
}

.mode-btn.active {
  border-color: var(--primary);
  background: var(--primary);
  color: #ffffff;
}

.mode-radio {
  display: none;
}

.mode-icon {
  flex-shrink: 0;
}

.mode-label {
  font-size: 13px;
  font-weight: 500;
}

.optimize-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.optimize-btn:hover:not(:disabled) {
  filter: brightness(1.1);
}

.optimize-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.results-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 24px;
}

@media (max-width: 1000px) {
  .results-layout {
    grid-template-columns: 1fr;
  }
}

.map-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.map-wrapper {
  height: 400px;
}

.details-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.details-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-stat {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  background: var(--bg);
  border-radius: var(--radius);
}

.stat-icon-svg {
  flex-shrink: 0;
  opacity: 0.7;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.legs-section {
  margin-top: 8px;
}

.legs-section h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.leg-card {
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
}

.leg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.leg-number {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.leg-mode {
  font-size: 11px;
  color: var(--accent);
  font-weight: 600;
  text-transform: uppercase;
}

.leg-details {
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.leg-divider {
  opacity: 0.3;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.empty-icon {
  opacity: 0.4;
  margin-bottom: 16px;
}

.empty-state .empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 14px;
  color: var(--text-secondary);
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
</style>
