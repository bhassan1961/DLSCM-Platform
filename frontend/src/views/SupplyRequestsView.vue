<template>
  <div class="supply-requests">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
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
        {{ $t('requests.newRequest') }}
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
          <option value="pending">{{ $t('requests.statusPending') }}</option>
          <option value="approved">{{ $t('requests.statusApproved') }}</option>
          <option value="sourcing">{{ $t('requests.statusSourcing') }}</option>
          <option value="dispatched">{{ $t('requests.statusDispatched') }}</option>
          <option value="delivered">{{ $t('requests.statusDelivered') }}</option>
        </select>
      </div>
      <div v-if="expandedRequest.notes" class="expanded-notes">
        {{ expandedRequest.notes }}
      </div>
      <div class="expanded-items" v-if="expandedRequest.items?.length">
        <h5>{{ $t('requests.requestedItems') }}</h5>
        <div class="item-row" v-for="(item, i) in expandedRequest.items" :key="i">
          <span class="item-name">{{ item.name || item.item_name }}</span>
          <span class="item-qty">x{{ item.quantity }}</span>
        </div>
      </div>
    </div>

    <!-- New Request Modal -->
    <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false" @keydown.escape="showModal = false">
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" ref="modalRef">
        <div class="modal-header">
          <h3 id="modal-title">{{ $t('requests.newSupplyRequest') }}</h3>
          <button class="modal-close" @click="showModal = false" :aria-label="$t('common.closeDialog')">&times;</button>
        </div>
        <form class="modal-form" @submit.prevent="submitRequest">
          <div class="form-group">
            <label for="req-title">{{ $t('requests.titleLabel') }}</label>
            <input id="req-title" v-model="form.title" required :placeholder="$t('requests.titlePlaceholder')" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="req-priority">{{ $t('requests.priority') }}</label>
              <select id="req-priority" v-model="form.priority" required>
                <option value="low">{{ $t('requests.priorityLow') }}</option>
                <option value="medium">{{ $t('requests.priorityMedium') }}</option>
                <option value="high">{{ $t('requests.priorityHigh') }}</option>
                <option value="critical">{{ $t('requests.priorityCritical') }}</option>
              </select>
            </div>
            <div class="form-group">
              <label for="req-disaster">{{ $t('requests.disaster') }}</label>
              <select id="req-disaster" v-model="form.disaster_id">
                <option value="">{{ $t('requests.selectDisaster') }}</option>
                <option v-for="d in disasters" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label for="req-destination">{{ $t('requests.destination') }}</label>
            <input id="req-destination" v-model="form.destination" :placeholder="$t('requests.destinationPlaceholder')" />
          </div>
          <div class="form-group">
            <label id="req-items-label">{{ $t('requests.items') }}</label>
            <div v-for="(item, i) in form.items" :key="i" class="item-input-row">
              <input v-model="item.name" :placeholder="$t('requests.itemNamePlaceholder')" />
              <input v-model.number="item.quantity" type="number" :placeholder="$t('requests.qtyPlaceholder')" min="1" />
              <button type="button" class="remove-item-btn" @click="form.items.splice(i, 1)">&times;</button>
            </div>
            <button type="button" class="add-item-btn" @click="form.items.push({ name: '', quantity: 1 })">
              {{ $t('requests.addItem') }}
            </button>
          </div>
          <div class="form-group">
            <label for="req-notes">{{ $t('common.notes') }}</label>
            <textarea id="req-notes" v-model="form.notes" rows="3" :placeholder="$t('requests.notesPlaceholder')"></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="cancel-btn" @click="showModal = false">{{ $t('common.cancel') }}</button>
            <button type="submit" class="submit-btn" :disabled="submitting">
              {{ submitting ? $t('requests.creating') : $t('requests.createRequest') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import DataTable from '../components/common/DataTable.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { requestsApi, disastersApi } from '../api/client'
import { saveOfflineRequest, getOfflineRequests } from '../services/offlineDb'
import { useOffline } from '../composables/useOffline'
import { useErrorHandler } from '../composables/useErrorHandler'

const { t } = useI18n()
const { online } = useOffline()
const { error, handleError, clearError } = useErrorHandler()

const statusTabs = computed(() => [
  { label: t('common.all'), value: '' },
  { label: t('requests.statusPending'), value: 'pending' },
  { label: t('requests.statusApproved'), value: 'approved' },
  { label: t('requests.statusSourcing'), value: 'sourcing' },
  { label: t('requests.statusDispatched'), value: 'dispatched' },
  { label: t('requests.statusDelivered'), value: 'delivered' }
])

const columns = computed(() => [
  { key: 'title', label: t('requests.titleLabel'), sortable: true },
  { key: 'priority', label: t('requests.priority'), sortable: true, width: '120px' },
  { key: 'status', label: t('common.status'), sortable: true, width: '130px' },
  { key: 'destination', label: t('requests.destination'), sortable: true },
  { key: 'requester', label: t('requests.requester'), sortable: true },
  { key: 'created_at', label: t('requests.created'), sortable: true, width: '140px' }
])

const requests = ref([])
const loading = ref(true)
const currentStatus = ref('')
const expandedRequest = ref(null)
const showModal = ref(false)
const submitting = ref(false)
const disasters = ref([])
const modalRef = ref(null)

watch(showModal, async (open) => {
  if (open) {
    await nextTick()
    const first = modalRef.value?.querySelector('input, select, textarea')
    first?.focus()
  }
})

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
    handleError(e, 'Failed to load requests')
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
    handleError(e, 'Failed to update status')
  }
}

async function submitRequest() {
  submitting.value = true
  try {
    const payload = {
      ...form.value,
      items: form.value.items.filter(i => i.name)
    }
    if (online.value) {
      await requestsApi.create(payload)
    } else {
      await saveOfflineRequest(payload)
    }
    showModal.value = false
    form.value = { title: '', priority: 'medium', disaster_id: '', destination: '', items: [{ name: '', quantity: 1 }], notes: '' }
    await filterByStatus(currentStatus.value)
  } catch (e) {
    if (!online.value) {
      await saveOfflineRequest({ ...form.value, items: form.value.items.filter(i => i.name) })
      showModal.value = false
      form.value = { title: '', priority: 'medium', disaster_id: '', destination: '', items: [{ name: '', quantity: 1 }], notes: '' }
    } else {
      handleError(e, 'Failed to create request')
    }
  } finally {
    submitting.value = false
  }
}

async function loadInitialData() {
  await filterByStatus('')
  try {
    const { data } = await disastersApi.list()
    disasters.value = data.disasters || data || []
  } catch (e) {
    handleError(e, 'Failed to load disasters')
  }
}

function retryLoad() {
  clearError()
  loadInitialData()
}

onMounted(loadInitialData)
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
  gap: 6px;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 7px 16px;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.tab-btn:hover {
  border-color: var(--accent);
  color: var(--text);
}

.tab-btn.active {
  background: var(--accent);
  color: #ffffff;
  border-color: var(--accent);
}

.new-request-btn {
  margin-left: auto;
  padding: 8px 20px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.15s ease;
  box-shadow: var(--shadow-sm);
}

.new-request-btn:hover {
  background: var(--accent-hover);
  box-shadow: var(--shadow);
}

.expanded-row {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: var(--shadow-sm);
}

.expanded-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
}

.expanded-header h4 {
  font-size: 16px;
  color: var(--text);
}

.status-select {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: 13px;
  transition: border-color 0.15s ease;
}

.status-select:focus {
  border-color: var(--accent);
}

.expanded-notes {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  line-height: 1.5;
}

.expanded-items h5 {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  margin-bottom: 4px;
  font-size: 14px;
}

.item-qty {
  font-weight: 600;
  color: var(--accent);
  font-variant-numeric: tabular-nums;
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: var(--surface);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border);
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
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--text-secondary);
  padding: 4px;
  line-height: 1;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
}

.modal-close:hover {
  background: var(--bg);
  color: var(--text);
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
  padding: 9px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: 14px;
  transition: border-color 0.15s ease;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  border-color: var(--accent);
}

.form-group textarea {
  resize: vertical;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 500px) {
  .form-row {
    grid-template-columns: 1fr;
  }
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
  transition: opacity 0.15s ease;
}

.remove-item-btn:hover {
  opacity: 0.7;
}

.add-item-btn {
  background: none;
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  width: 100%;
  transition: all 0.15s ease;
}

.add-item-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
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
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 14px;
  transition: all 0.15s ease;
}

.cancel-btn:hover {
  border-color: var(--text-secondary);
  color: var(--text);
}

.submit-btn {
  padding: 8px 24px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.15s ease;
  box-shadow: var(--shadow-sm);
}

.submit-btn:hover {
  background: var(--accent-hover);
  box-shadow: var(--shadow);
}

.submit-btn:disabled {
  opacity: 0.6;
}

@media (max-width: 600px) {
  .status-tabs {
    gap: 4px;
  }

  .tab-btn {
    padding: 6px 12px;
    font-size: 12px;
  }

  .new-request-btn {
    width: 100%;
    margin-left: 0;
    text-align: center;
  }
}
</style>
