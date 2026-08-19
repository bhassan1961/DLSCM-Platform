<template>
  <div class="shipments">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <!-- Header with Add button -->
    <div class="page-actions">
      <button class="btn-primary" @click="showModal = true">+ {{ $t('shipments.newShipment') }}</button>
    </div>

    <!-- Map -->
    <div class="map-section">
      <div class="section-header">
        <h2 class="panel-title">{{ $t('shipments.trackingMap') }}</h2>
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
      <template #cell-status="{ value, row }">
        <select
          class="status-select"
          :value="value"
          @change="updateStatus(row.id, $event.target.value)"
          @click.stop
        >
          <option value="preparing">Preparing</option>
          <option value="in_transit">In Transit</option>
          <option value="delivered">Delivered</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </template>
      <template #cell-eta="{ value }">
        {{ formatDate(value) }}
      </template>
      <template #cell-departed_at="{ value }">
        {{ formatDate(value) }}
      </template>
      <template #cell-actions="{ row }">
        <button class="btn-icon-danger" @click.stop="deleteShipment(row.id)" title="Delete">&#10005;</button>
      </template>
    </DataTable>

    <!-- Create Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" @keydown.escape="showModal = false">
        <div class="modal-header">
          <h3 id="modal-title">New Shipment</h3>
          <button class="modal-close" @click="showModal = false" aria-label="Close dialog">&times;</button>
        </div>
        <form @submit.prevent="createShipment" class="modal-body">
          <div class="form-group">
            <label for="ship-disaster">Disaster</label>
            <select id="ship-disaster" v-model="form.disaster_id" required>
              <option :value="null" disabled>Select disaster...</option>
              <option v-for="d in disasters" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="ship-origin">Origin</label>
              <input id="ship-origin" v-model="form.origin" required placeholder="e.g. Nairobi Hub" />
            </div>
            <div class="form-group">
              <label for="ship-destination">Destination</label>
              <input id="ship-destination" v-model="form.destination" required placeholder="e.g. Turkana Camp" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="ship-carrier">Carrier</label>
              <input id="ship-carrier" v-model="form.carrier" placeholder="e.g. WFP Fleet" />
            </div>
            <div class="form-group">
              <label for="ship-mode">Transport Mode</label>
              <select id="ship-mode" v-model="form.transport_mode">
                <option value="road">Road</option>
                <option value="air">Air</option>
                <option value="sea">Sea</option>
                <option value="rail">Rail</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label for="ship-items">Items Description</label>
            <input id="ship-items" v-model="form.items_description" placeholder="e.g. Medical supplies, shelter kits" />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showModal = false">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="creating">{{ creating ? 'Creating...' : 'Create Shipment' }}</button>
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
import { shipmentsApi, disastersApi } from '../api/client'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const columns = [
  { key: 'tracking_id', label: 'Tracking ID', sortable: true },
  { key: 'status', label: 'Status', sortable: true, width: '150px' },
  { key: 'mode', label: 'Mode', sortable: true },
  { key: 'carrier', label: 'Carrier', sortable: true },
  { key: 'eta', label: 'ETA', sortable: true, width: '140px' },
  { key: 'departed_at', label: 'Departed', sortable: true, width: '140px' },
  { key: 'actions', label: '', width: '50px' }
]

const shipments = ref([])
const disasters = ref([])
const loading = ref(true)
const showModal = ref(false)
const creating = ref(false)

const form = ref({
  disaster_id: null,
  origin: '',
  destination: '',
  carrier: '',
  transport_mode: 'road',
  items_description: ''
})

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

async function createShipment() {
  creating.value = true
  try {
    await shipmentsApi.create(form.value)
    showModal.value = false
    form.value = { disaster_id: null, origin: '', destination: '', carrier: '', transport_mode: 'road', items_description: '' }
    await reload()
  } catch (e) {
    handleError(e, 'Failed to create shipment')
  } finally {
    creating.value = false
  }
}

async function updateStatus(id, status) {
  try {
    await shipmentsApi.updateStatus(id, status)
    const s = shipments.value.find(s => s.id === id)
    if (s) s.status = status
  } catch (e) {
    handleError(e, 'Failed to update status')
  }
}

async function deleteShipment(id) {
  try {
    await shipmentsApi.delete(id)
    shipments.value = shipments.value.filter(s => s.id !== id)
  } catch (e) {
    handleError(e, 'Failed to delete shipment')
  }
}

async function reload() {
  loading.value = true
  try {
    const { data } = await shipmentsApi.list()
    const raw = data.shipments || data || []
    shipments.value = raw.map(s => ({
      ...s,
      mode: s.transport_mode || s.mode || '',
    }))
  } catch (e) {
    handleError(e, 'Failed to load shipments')
  } finally {
    loading.value = false
  }
}

async function loadInitialData() {
  const [, disasterRes] = await Promise.allSettled([
    reload(),
    disastersApi.list()
  ])
  if (disasterRes.status === 'fulfilled') {
    disasters.value = disasterRes.value.data?.disasters || disasterRes.value.data || []
  }
}

function retryLoad() {
  clearError()
  loadInitialData()
}

onMounted(loadInitialData)
</script>

<style scoped>
.shipments {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-actions {
  display: flex;
  justify-content: flex-end;
}

.map-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.section-header {
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
}

.section-header .panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: 0.01em;
}

.map-wrapper {
  height: 350px;
}

.status-select {
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: 12px;
  cursor: pointer;
}

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
  max-width: 520px;
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
  padding: 4px;
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

@media (max-width: 600px) {
  .map-wrapper {
    height: 240px;
  }
  .form-row {
    flex-direction: column;
  }
}
</style>
