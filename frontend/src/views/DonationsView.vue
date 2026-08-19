<template>
  <div class="donations-view">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="page-header">
      <div>
        <h2>{{ $t('donations.title') }}</h2>
        <p class="subtitle">{{ $t('donations.subtitle') }}</p>
      </div>
      <button class="action-btn" @click="showForm = !showForm">
        {{ showForm ? $t('common.cancel') : $t('donations.recordDonation') }}
      </button>
    </div>

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
    </div>

    <!-- Inline Form -->
    <div v-if="showForm" class="form-panel">
      <h3>{{ $t('donations.recordDonation') }}</h3>
      <form @submit.prevent="submitDonation">
        <div class="form-grid">
          <div class="form-group">
            <label for="don-name">{{ $t('donations.donorName') }}</label>
            <input id="don-name" v-model="form.donor_name" required :placeholder="$t('donations.donorNamePlaceholder')" />
          </div>
          <div class="form-group">
            <label for="don-contact">{{ $t('donations.donorContact') }}</label>
            <input id="don-contact" v-model="form.donor_contact" :placeholder="$t('donations.donorContactPlaceholder')" />
          </div>
          <div class="form-group">
            <label for="don-category">{{ $t('common.category') }}</label>
            <select id="don-category" v-model="form.category" required>
              <option value="">{{ $t('donations.selectCategory') }}</option>
              <option value="food">{{ $t('donations.categoryFood') }}</option>
              <option value="medical">{{ $t('donations.categoryMedical') }}</option>
              <option value="clothing">{{ $t('donations.categoryClothing') }}</option>
              <option value="shelter">{{ $t('donations.categoryShelter') }}</option>
              <option value="water">{{ $t('donations.categoryWater') }}</option>
              <option value="nfi">{{ $t('donations.categoryNfi') }}</option>
              <option value="other">{{ $t('donations.categoryOther') }}</option>
            </select>
          </div>
          <div class="form-group">
            <label for="don-qty">{{ $t('common.quantity') }}</label>
            <input id="don-qty" v-model.number="form.quantity" type="number" min="1" :placeholder="$t('donations.amountPlaceholder')" />
          </div>
          <div class="form-group">
            <label for="don-unit">{{ $t('common.unit') }}</label>
            <input id="don-unit" v-model="form.unit" :placeholder="$t('donations.unitPlaceholder')" />
          </div>
        </div>
        <div class="form-group">
          <label for="don-desc">{{ $t('donations.itemsDescription') }}</label>
          <textarea id="don-desc" v-model="form.items_description" rows="3" required :placeholder="$t('donations.itemsDescriptionPlaceholder')"></textarea>
        </div>
        <div class="form-group">
          <label for="don-notes">{{ $t('common.notes') }}</label>
          <textarea id="don-notes" v-model="form.notes" rows="2" :placeholder="$t('donations.additionalNotesPlaceholder')"></textarea>
        </div>
        <div class="form-actions">
          <button type="button" class="cancel-btn" @click="showForm = false">{{ $t('common.cancel') }}</button>
          <button type="submit" class="submit-btn" :disabled="submitting">
            {{ submitting ? $t('common.saving') : $t('donations.recordDonation') }}
          </button>
        </div>
      </form>
    </div>

    <!-- Donations Table -->
    <DataTable :columns="columns" :rows="donations" :loading="loading">
      <template #cell-quality_status="{ value }">
        <span class="quality-badge" :class="qualityClass(value)">
          {{ formatQuality(value) }}
        </span>
      </template>
      <template #cell-status="{ value }">
        <StatusBadge :status="value" />
      </template>
      <template #cell-received_at="{ value }">
        {{ formatDate(value) }}
      </template>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DataTable from '../components/common/DataTable.vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import { donationsApi } from '../api/client'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const statusTabs = [
  { label: 'All', value: '' },
  { label: 'Received', value: 'received' },
  { label: 'Assessed', value: 'assessed' },
  { label: 'Stored', value: 'stored' },
  { label: 'Distributed', value: 'distributed' },
  { label: 'Rejected', value: 'rejected' }
]

const columns = [
  { key: 'donor_name', label: 'Donor', sortable: true },
  { key: 'items_description', label: 'Items', sortable: false },
  { key: 'category', label: 'Category', sortable: true, width: '110px' },
  { key: 'quantity', label: 'Qty', sortable: true, width: '80px' },
  { key: 'quality_status', label: 'Quality', sortable: true, width: '150px' },
  { key: 'warehouse', label: 'Warehouse', sortable: true, width: '130px' },
  { key: 'received_at', label: 'Received', sortable: true, width: '130px' },
  { key: 'status', label: 'Status', sortable: true, width: '120px' }
]

const donations = ref([])
const loading = ref(true)
const currentStatus = ref('')
const showForm = ref(false)
const submitting = ref(false)

const form = ref({
  donor_name: '', donor_contact: '', items_description: '',
  category: '', quantity: null, unit: '', notes: ''
})

const qualityColors = {
  pending_assessment: 'quality-grey',
  acceptable: 'quality-green',
  requires_sorting: 'quality-yellow',
  rejected: 'quality-red'
}

function qualityClass(val) {
  return qualityColors[val] || 'quality-grey'
}

function formatQuality(val) {
  if (!val) return 'Pending'
  return val.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function formatDate(ts) {
  if (!ts) return '-'
  return new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

async function filterByStatus(status) {
  currentStatus.value = status
  loading.value = true
  try {
    const { data } = await donationsApi.list(status || undefined)
    donations.value = data.donations || data || []
  } catch (e) {
    handleError(e, 'Failed to load donations')
  } finally {
    loading.value = false
  }
}

async function submitDonation() {
  submitting.value = true
  try {
    await donationsApi.create(form.value)
    showForm.value = false
    form.value = {
      donor_name: '', donor_contact: '', items_description: '',
      category: '', quantity: null, unit: '', notes: ''
    }
    await filterByStatus(currentStatus.value)
  } catch (e) {
    handleError(e, 'Failed to record donation')
  } finally {
    submitting.value = false
  }
}

function retryLoad() {
  clearError()
  filterByStatus(currentStatus.value)
}

onMounted(() => {
  filterByStatus('')
})
</script>

<style scoped>
.donations-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.page-header h2 {
  font-size: 22px;
  color: var(--text);
  margin: 0;
}

.subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.action-btn {
  padding: 8px 20px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.action-btn:hover { opacity: 0.9; }

.status-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
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

.form-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
}

.form-panel h3 {
  font-size: 16px;
  color: var(--text);
  margin: 0 0 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
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
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  box-sizing: border-box;
}

.form-group textarea { resize: vertical; }

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}

.cancel-btn {
  padding: 8px 20px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
}

.submit-btn {
  padding: 8px 24px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--primary);
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.submit-btn:disabled { opacity: 0.6; }

.quality-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--radius);
  font-size: 12px;
  font-weight: 600;
}

.quality-grey {
  background: rgba(127, 127, 127, 0.12);
  color: var(--text-secondary);
}

.quality-green {
  background: rgba(39, 174, 96, 0.12);
  color: var(--success);
}

.quality-yellow {
  background: rgba(243, 156, 18, 0.12);
  color: var(--warning);
}

.quality-red {
  background: rgba(231, 76, 60, 0.12);
  color: var(--danger);
}
</style>
