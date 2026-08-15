<template>
  <div class="supply-requests">
    <!-- Status Tabs -->
    <div class="status-tabs">
      <button
        v-for="tab in statusTabs"
        :key="tab.value"
        class="tab-btn"
        :class="{ active: currentStatus === tab.value }"
        @click="filterByStatus(tab.value)"
      >
        {{ tab.label }}
      </button>
      <button class="new-request-btn" @click="showModal = true">
        + New Request
      </button>
    </div>

    <!-- Requests Table -->
    <DataTable
      :columns="columns"
      :rows="requests"
      :loading="loading"
      @row-click="toggleExpand"
    >
      <template #cell-priority="{ value }">
        <StatusBadge :status="value" size="sm" />
      </template>
      <template #cell-status="{ value }">
        <StatusBadge :status="value" />
      </template>
      <template #cell-created_at="{ value }">
        {{ formatDate(value) }}
      </template>
    </DataTable>

    <!-- Expanded Row -->
    <div v-if="expandedRequest" class="expanded-row">
      <div class="expanded-header">
        <h4>{{ expandedRequest.title }}</h4>
        <select
          class="status-select"
          :value="expandedRequest.status"
          @change="changeStatus(expandedRequest.id, $event.target.value)"
        >
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="sourcing">Sourcing</option>
          <option value="dispatched">Dispatched</option>
          <option value="delivered">Delivered</option>
        </select>
      </div>
      <div v-if="expandedRequest.notes" class="expanded-notes">
        {{ expandedRequest.notes }}
      </div>
      <div class="expanded-items" v-if="expandedRequest.items?.length">
        <h5>Requested Items</h5>
        <div class="item-row" v-for="(item, i) in expandedRequest.items" :key="i">
          <span class="item-name">{{ item.name || item.item_name }}</span>
          <span class="item-qty">x{{ item.quantity }}</span>
        </div>
      </div>
    </div>

    <!-- New Request Modal -->
    <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>New Supply Request</h3>
          <button class="modal-close" @click="showModal = false">&times;</button>
        </div>
        <form class="modal-form" @submit.prevent="submitRequest">
          <div class="form-group">
            <label>Title</label>
            <input v-model="form.title" required placeholder="Request title" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Priority</label>
              <select v-model="form.priority" required>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div class="form-group">
              <label>Disaster</label>
              <select v-model="form.disaster_id">
                <option value="">Select disaster</option>
                <option v-for="d in disasters" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>Destination</label>
            <input v-model="form.destination" placeholder="Delivery location" />
          </div>
          <div class="form-group">
            <label>Items</label>
            <div v-for="(item, i) in form.items" :key="i" class="item-input-row">
              <input v-model="item.name" placeholder="Item name" />
              <input v-model.number="item.quantity" type="number" placeholder="Qty" min="1" />
              <button type="button" class="remove-item-btn" @click="form.items.splice(i, 1)">&times;</button>
            </div>
            <button type="button" class="add-item-btn" @click="form.items.push({ name: '', quantity: 1 })">
              + Add Item
            </button>
          </div>
          <div class="form-group">
            <label>Notes</label>
            <textarea v-model="form.notes" rows="3" placeholder="Additional notes"></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="cancel-btn" @click="showModal = false">Cancel</button>
            <button type="submit" class="submit-btn" :disabled="submitting">
              {{ submitting ? 'Creating...' : 'Create Request' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DataTable from '../components/common/DataTable.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import { requestsApi, disastersApi } from '../api/client'

const statusTabs = [
  { label: 'All', value: '' },
  { label: 'Pending', value: 'pending' },
  { label: 'Approved', value: 'approved' },
  { label: 'Sourcing', value: 'sourcing' },
  { label: 'Dispatched', value: 'dispatched' },
  { label: 'Delivered', value: 'delivered' }
]

const columns = [
  { key: 'title', label: 'Title', sortable: true },
  { key: 'priority', label: 'Priority', sortable: true, width: '120px' },
  { key: 'status', label: 'Status', sortable: true, width: '130px' },
  { key: 'destination', label: 'Destination', sortable: true },
  { key: 'requester', label: 'Requester', sortable: true },
  { key: 'created_at', label: 'Created', sortable: true, width: '140px' }
]

const requests = ref([])
const loading = ref(true)
const currentStatus = ref('')
const expandedRequest = ref(null)
const showModal = ref(false)
const submitting = ref(false)
const disasters = ref([])

const form = ref({
  title: '',
  priority: 'medium',
  disaster_id: '',
  destination: '',
  items: [{ name: '', quantity: 1 }],
  notes: ''
})

function formatDate(ts) {
  if (!ts) return '-'
  return new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function toggleExpand(row) {
  expandedRequest.value = expandedRequest.value?.id === row.id ? null : row
}

async function filterByStatus(status) {
  currentStatus.value = status
  loading.value = true
  try {
    const { data } = await requestsApi.list(status || undefined)
    const raw = data.requests || data || []
    requests.value = raw.map(r => ({
      ...r,
      destination: r.destination_name || '',
      requester: r.requester_name || '',
      items: (r.items || []).map(i => ({
        ...i,
        name: i.item_name || '',
        quantity: i.quantity_requested || 0,
      })),
    }))
  } catch (e) {
    console.error('Failed to load requests:', e)
  } finally {
    loading.value = false
  }
}

async function changeStatus(id, status) {
  try {
    await requestsApi.updateStatus(id, status)
    await filterByStatus(currentStatus.value)
    expandedRequest.value = null
  } catch (e) {
    console.error('Failed to update status:', e)
  }
}

async function submitRequest() {
  submitting.value = true
  try {
    const payload = {
      ...form.value,
      items: form.value.items.filter(i => i.name)
    }
    await requestsApi.create(payload)
    showModal.value = false
    form.value = { title: '', priority: 'medium', disaster_id: '', destination: '', items: [{ name: '', quantity: 1 }], notes: '' }
    await filterByStatus(currentStatus.value)
  } catch (e) {
    console.error('Failed to create request:', e)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await filterByStatus('')
  try {
    const { data } = await disastersApi.list()
    disasters.value = data.disasters || data || []
  } catch (e) {
    console.error('Failed to load disasters:', e)
  }
})
</script>

<style scoped>
.supply-requests {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.tab-btn:hover {
  border-color: var(--primary);
  color: var(--text);
}

.tab-btn.active {
  background: var(--primary);
  color: #ffffff;
  border-color: var(--primary);
}

.new-request-btn {
  margin-left: auto;
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  background: var(--accent);
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
  transition: opacity 0.15s ease;
}

.new-request-btn:hover {
  opacity: 0.9;
}

.expanded-row {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px;
}

.expanded-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.expanded-header h4 {
  font-size: 16px;
  color: var(--text);
}

.status-select {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--text);
  font-size: 13px;
}

.expanded-notes {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.expanded-items h5 {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: var(--bg);
  border-radius: 4px;
  margin-bottom: 4px;
  font-size: 14px;
}

.item-qty {
  font-weight: 600;
  color: var(--accent);
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--surface);
  border-radius: 12px;
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border);
}

.modal-header h3 {
  font-size: 18px;
  color: var(--text);
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--text-secondary);
  padding: 0;
  line-height: 1;
}

.modal-form {
  padding: 24px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 6px;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--text);
  font-size: 14px;
}

.form-group textarea {
  resize: vertical;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.item-input-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.item-input-row input:first-child {
  flex: 1;
}

.item-input-row input:nth-child(2) {
  width: 80px;
}

.remove-item-btn {
  background: none;
  border: none;
  color: var(--danger);
  font-size: 18px;
  padding: 0 4px;
}

.add-item-btn {
  background: none;
  border: 1px dashed var(--border);
  border-radius: 4px;
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  width: 100%;
}

.add-item-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.cancel-btn {
  padding: 8px 20px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 14px;
}

.submit-btn {
  padding: 8px 24px;
  border: none;
  border-radius: 6px;
  background: var(--primary);
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
}

.submit-btn:disabled {
  opacity: 0.6;
}
</style>
