<template>
  <div class="shipments">
    <!-- Map -->
    <div class="map-section">
      <div class="section-header">
        <h3>Shipment Tracking Map</h3>
      </div>
      <div class="map-wrapper">
        <MapView
          :markers="mapMarkers"
          :polylines="mapPolylines"
          :center="[20, 0]"
          :zoom="2"
        />
      </div>
    </div>

    <!-- Shipments Table -->
    <DataTable
      :columns="columns"
      :rows="shipments"
      :loading="loading"
      @row-click="() => {}"
    >
      <template #cell-status="{ value }">
        <StatusBadge :status="value" />
      </template>
      <template #cell-eta="{ value }">
        {{ formatDate(value) }}
      </template>
      <template #cell-departed_at="{ value }">
        {{ formatDate(value) }}
      </template>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import MapView from '../components/common/MapView.vue'
import DataTable from '../components/common/DataTable.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import { shipmentsApi } from '../api/client'

const columns = [
  { key: 'tracking_id', label: 'Tracking ID', sortable: true },
  { key: 'status', label: 'Status', sortable: true, width: '130px' },
  { key: 'mode', label: 'Mode', sortable: true },
  { key: 'carrier', label: 'Carrier', sortable: true },
  { key: 'eta', label: 'ETA', sortable: true, width: '140px' },
  { key: 'departed_at', label: 'Departed', sortable: true, width: '140px' }
]

const shipments = ref([])
const loading = ref(true)

const mapMarkers = computed(() => {
  return shipments.value
    .filter(s => s.current_lat && s.current_lng)
    .map(s => ({
      lat: s.current_lat,
      lng: s.current_lng,
      label: s.tracking_id,
      color: s.status === 'delivered' ? 'green' : 'amber',
      popup: `<strong>${s.tracking_id}</strong><br>${s.carrier || ''}<br>Status: ${s.status}`
    }))
})

const mapPolylines = computed(() => {
  return shipments.value
    .filter(s => s.legs?.length)
    .flatMap(s => s.legs.map(leg => ({
      points: [[leg.from_lat, leg.from_lng], [leg.to_lat, leg.to_lng]],
      color: s.status === 'delivered' ? 'green' : '#e8913a'
    })))
})

function formatDate(ts) {
  if (!ts) return '-'
  return new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

onMounted(async () => {
  try {
    const { data } = await shipmentsApi.list()
    const raw = data.shipments || data || []
    shipments.value = raw.map(s => ({
      ...s,
      mode: s.transport_mode || s.mode || '',
    }))
  } catch (e) {
    console.error('Failed to load shipments:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.shipments {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.map-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.section-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.section-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.map-wrapper {
  height: 350px;
}
</style>
