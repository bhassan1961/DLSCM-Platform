<template>
  <div class="dashboard">
    <!-- Stat Cards Row -->
    <div class="stats-row">
      <StatCard
        label="Active Disasters"
        :value="stats.active_disasters ?? '-'"
        icon="&#x26A0;"
        color="var(--danger)"
      />
      <StatCard
        label="Pending Requests"
        :value="stats.pending_requests ?? '-'"
        icon="&#x2709;"
        color="var(--warning)"
      />
      <StatCard
        label="In-Transit Shipments"
        :value="stats.in_transit_shipments ?? '-'"
        icon="&#x1F69A;"
        color="var(--accent)"
      />
      <StatCard
        label="Active Alerts"
        :value="stats.active_alerts ?? '-'"
        icon="&#x1F514;"
        color="var(--primary)"
      />
    </div>

    <!-- Main Content -->
    <div class="dashboard-main">
      <!-- Map -->
      <div class="map-panel">
        <div class="panel-header">
          <h3>Global Operations Map</h3>
        </div>
        <div class="map-wrapper">
          <MapView
            :markers="mapMarkers"
            :center="[20, 0]"
            :zoom="2"
          />
        </div>
      </div>

      <!-- Alerts Panel -->
      <div class="alerts-panel">
        <div class="panel-header">
          <h3>Active Alerts</h3>
          <span class="alert-count">{{ alerts.length }}</span>
        </div>
        <div class="alerts-list">
          <div v-if="alertsLoading" class="loading-state">
            <div class="spinner"></div>
          </div>
          <div v-else-if="!alerts.length" class="empty-state">
            No active alerts
          </div>
          <div
            v-for="alert in alerts"
            :key="alert.id"
            class="alert-item"
          >
            <div class="alert-top">
              <StatusBadge :status="alert.severity" size="sm" />
              <span class="alert-time">{{ formatTime(alert.created_at) }}</span>
            </div>
            <div class="alert-title">{{ alert.title }}</div>
            <div class="alert-desc">{{ truncate(alert.description, 100) }}</div>
            <button
              v-if="!alert.acknowledged"
              class="ack-btn"
              @click="acknowledgeAlert(alert.id)"
            >
              Acknowledge
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import StatCard from '../components/common/StatCard.vue'
import MapView from '../components/common/MapView.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import { dashboardApi, disastersApi, alertsApi, inventoryApi } from '../api/client'

const stats = ref({})
const disasters = ref([])
const warehouses = ref([])
const alerts = ref([])
const alertsLoading = ref(true)

const mapMarkers = computed(() => {
  const disasterMarkers = disasters.value
    .filter(d => d.latitude && d.longitude)
    .map(d => ({
      lat: d.latitude,
      lng: d.longitude,
      label: d.name,
      color: 'red',
      radius: 10,
      popup: `<strong>${d.name}</strong><br>${d.type || ''} - ${d.severity || ''}`
    }))
  const warehouseMarkers = warehouses.value
    .filter(w => w.latitude && w.longitude)
    .map(w => ({
      lat: w.latitude,
      lng: w.longitude,
      label: w.name,
      color: 'blue',
      radius: 7,
      popup: `<strong>${w.name}</strong><br>${w.location || ''}`
    }))
  return [...disasterMarkers, ...warehouseMarkers]
})

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function truncate(text, len) {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}

async function acknowledgeAlert(id) {
  try {
    await alertsApi.acknowledge(id)
    alerts.value = alerts.value.filter(a => a.id !== id)
  } catch (e) {
    console.error('Failed to acknowledge alert:', e)
  }
}

onMounted(async () => {
  try {
    const [statsRes, disastersRes, warehousesRes, alertsRes] = await Promise.allSettled([
      dashboardApi.stats(),
      disastersApi.list('active'),
      inventoryApi.warehouses(),
      alertsApi.list()
    ])
    if (statsRes.status === 'fulfilled') stats.value = statsRes.value.data || {}
    if (disastersRes.status === 'fulfilled') disasters.value = disastersRes.value.data?.disasters || disastersRes.value.data || []
    if (warehousesRes.status === 'fulfilled') warehouses.value = warehousesRes.value.data?.warehouses || warehousesRes.value.data || []
    if (alertsRes.status === 'fulfilled') alerts.value = alertsRes.value.data?.alerts || alertsRes.value.data || []
  } catch (e) {
    console.error('Dashboard load error:', e)
  } finally {
    alertsLoading.value = false
  }
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

.dashboard-main {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
}

@media (max-width: 1200px) {
  .dashboard-main {
    grid-template-columns: 1fr;
  }
}

.map-panel,
.alerts-panel {
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

.alert-count {
  background: var(--danger);
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
  min-width: 22px;
  height: 22px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
}

.map-wrapper {
  height: 400px;
}

.alerts-list {
  max-height: 400px;
  overflow-y: auto;
}

.alert-item {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.alert-item:last-child {
  border-bottom: none;
}

.alert-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.alert-time {
  font-size: 11px;
  color: var(--text-secondary);
}

.alert-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text);
  margin-bottom: 4px;
}

.alert-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
  margin-bottom: 8px;
}

.ack-btn {
  padding: 4px 12px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 12px;
  transition: all 0.15s ease;
}

.ack-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.loading-state,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  color: var(--text-secondary);
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
