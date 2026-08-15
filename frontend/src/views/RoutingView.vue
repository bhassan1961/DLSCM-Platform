<template>
  <div class="routing">
    <!-- Controls Panel -->
    <div class="controls-panel">
      <div class="panel-header">
        <h3>Route Parameters</h3>
      </div>
      <div class="controls-body">
        <div class="control-row">
          <div class="control-group">
            <label class="control-label">Origin Warehouse</label>
            <select v-model="selectedWarehouse" class="control-select">
              <option :value="null" disabled>Select warehouse...</option>
              <option v-for="w in warehouses" :key="w.id" :value="w">
                {{ w.name }} ({{ w.location }})
              </option>
            </select>
          </div>
          <div class="control-group">
            <label class="control-label">Destination Disaster</label>
            <select v-model="selectedDisaster" class="control-select">
              <option :value="null" disabled>Select destination...</option>
              <option v-for="d in disasters" :key="d.id" :value="d">
                {{ d.name }}
              </option>
            </select>
          </div>
        </div>

        <div class="control-row">
          <div class="control-group">
            <label class="control-label">Transport Mode</label>
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
                <span class="mode-icon">{{ m.icon }}</span>
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
              {{ loading ? 'Optimizing...' : 'Optimize Route' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="error-banner">
      {{ error }}
    </div>

    <!-- Results -->
    <div class="results-layout" v-if="result || selectedWarehouse || selectedDisaster">
      <!-- Map -->
      <div class="map-panel">
        <div class="panel-header">
          <h3>Route Map</h3>
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
          <h3>Route Summary</h3>
        </div>
        <div class="details-body">
          <div class="detail-stat">
            <div class="stat-icon">&#x1F4CF;</div>
            <div class="stat-info">
              <div class="stat-value">{{ result.total_distance_km?.toFixed(1) }} km</div>
              <div class="stat-label">Total Distance</div>
            </div>
          </div>
          <div class="detail-stat">
            <div class="stat-icon">&#x23F1;</div>
            <div class="stat-info">
              <div class="stat-value">{{ formatDuration(result.total_duration_hours) }}</div>
              <div class="stat-label">Estimated Duration</div>
            </div>
          </div>
          <div class="detail-stat">
            <div class="stat-icon">{{ modeIcon }}</div>
            <div class="stat-info">
              <div class="stat-value">{{ formatMode(result.mode) }}</div>
              <div class="stat-label">Transport Mode</div>
            </div>
          </div>

          <!-- Legs -->
          <div class="legs-section" v-if="result.legs?.length">
            <h4>Route Legs</h4>
            <div
              v-for="(leg, idx) in result.legs"
              :key="idx"
              class="leg-card"
            >
              <div class="leg-header">
                <span class="leg-number">Leg {{ idx + 1 }}</span>
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
      <span class="empty-icon">&#x1F6E3;</span>
      <h3>Plan an optimal delivery route</h3>
      <p>Select an origin warehouse, destination, and transport mode to calculate the best route.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import MapView from '../components/common/MapView.vue'
import { inventoryApi, disastersApi, routingApi } from '../api/client'

const warehouses = ref([])
const disasters = ref([])
const selectedWarehouse = ref(null)
const selectedDisaster = ref(null)
const selectedMode = ref('road')
const loading = ref(false)
const error = ref(null)
const result = ref(null)

const modes = [
  { value: 'road', label: 'Road', icon: '\u{1F69A}' },
  { value: 'air', label: 'Air', icon: '\u{2708}' },
  { value: 'sea', label: 'Sea', icon: '\u{1F6A2}' }
]

const canOptimize = computed(() => {
  return selectedWarehouse.value && selectedDisaster.value
})

const modeIcon = computed(() => {
  const m = modes.find(m => m.value === result.value?.mode)
  return m?.icon || '\u{1F69A}'
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
  error.value = null
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
    error.value = 'Failed to optimize route. Please try again.'
    console.error('Routing error:', e)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
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
    console.error('Failed to load data:', e)
  }
})
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
  border-radius: 8px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.panel-header h3 {
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
  border-radius: 6px;
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
  border-radius: 6px;
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
  font-size: 16px;
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
  border-radius: 6px;
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
  border-radius: 8px;
  overflow: hidden;
}

.map-wrapper {
  height: 400px;
}

.details-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
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
  border-radius: 8px;
}

.stat-icon {
  font-size: 24px;
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
  border-radius: 6px;
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
  font-size: 48px;
  opacity: 0.5;
  margin-bottom: 16px;
}

.empty-state h3 {
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
</style>
