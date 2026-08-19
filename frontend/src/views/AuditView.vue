<template>
  <div class="audit-view">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="page-header">
      <div>
        <h2>{{ $t('audit.title') }}</h2>
        <p class="subtitle">{{ $t('audit.subtitle') }}</p>
      </div>
    </div>

    <!-- Filter -->
    <div class="filter-bar">
      <select v-model="selectedType" class="filter-select" @change="loadAudit">
        <option value="">{{ $t('audit.allResourceTypes') }}</option>
        <option v-for="rt in resourceTypes" :key="rt" :value="rt">{{ formatType(rt) }}</option>
      </select>
    </div>

    <!-- Audit Table -->
    <DataTable :columns="columns" :rows="entries" :loading="loading">
      <template #cell-timestamp="{ value }">
        {{ formatTimestamp(value) }}
      </template>
      <template #cell-action="{ value }">
        <span class="action-badge" :class="actionClass(value)">{{ value }}</span>
      </template>
      <template #cell-resource_type="{ value }">
        <span class="resource-type">{{ formatType(value) }}</span>
      </template>
      <template #cell-details="{ value }">
        <span class="details-text">{{ truncate(value, 80) }}</span>
      </template>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DataTable from '../components/common/DataTable.vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { auditApi } from '../api/client'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const resourceTypes = [
  'supply_request', 'stock', 'shipment', 'supplier',
  'donation', 'kit', 'warehouse', 'disaster', 'user'
]

const columns = [
  { key: 'timestamp', label: 'Timestamp', sortable: true, width: '180px' },
  { key: 'action', label: 'Action', sortable: true, width: '100px' },
  { key: 'resource_type', label: 'Resource Type', sortable: true, width: '140px' },
  { key: 'resource_id', label: 'Resource ID', sortable: false, width: '100px' },
  { key: 'user_email', label: 'User', sortable: true, width: '140px' },
  { key: 'details', label: 'Details' }
]

const entries = ref([])
const loading = ref(true)
const selectedType = ref('')

function formatType(val) {
  if (!val) return '-'
  return val.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function actionClass(action) {
  const map = { create: 'action-create', update: 'action-update', delete: 'action-delete' }
  return map[action] || 'action-default'
}

function truncate(val, max) {
  if (!val) return '-'
  const str = typeof val === 'object' ? JSON.stringify(val) : String(val)
  return str.length > max ? str.slice(0, max) + '...' : str
}

function formatTimestamp(ts) {
  if (!ts) return '-'
  const date = new Date(ts)
  const now = new Date()
  const diffMs = now - date
  const diffMin = Math.floor(diffMs / 60000)

  if (diffMin < 1) return 'Just now'
  if (diffMin < 60) return diffMin + ' min ago'
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return diffHr + (diffHr === 1 ? ' hour ago' : ' hours ago')
  const diffDay = Math.floor(diffHr / 24)
  if (diffDay < 7) return diffDay + (diffDay === 1 ? ' day ago' : ' days ago')

  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

async function loadAudit() {
  loading.value = true
  try {
    const { data } = await auditApi.list(selectedType.value || undefined)
    const raw = Array.isArray(data) ? data : (data.logs || data.audit || [])
    entries.value = raw.sort((a, b) => {
      const ta = new Date(a.timestamp || 0)
      const tb = new Date(b.timestamp || 0)
      return tb - ta
    })
  } catch (e) {
    handleError(e, 'Failed to load audit entries')
  } finally {
    loading.value = false
  }
}

function retryLoad() {
  clearError()
  loadAudit()
}

onMounted(() => {
  loadAudit()
})
</script>

<style scoped>
.audit-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
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

.filter-bar {
  display: flex;
  gap: 12px;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: 13px;
  min-width: 200px;
}

.action-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--radius);
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
}

.action-create {
  background: rgba(39, 174, 96, 0.12);
  color: var(--success);
}

.action-update {
  background: rgba(30, 58, 95, 0.12);
  color: var(--primary);
}

.action-delete {
  background: rgba(231, 76, 60, 0.12);
  color: var(--danger);
}

.action-default {
  background: rgba(127, 127, 127, 0.12);
  color: var(--text-secondary);
}

.resource-type {
  font-size: 13px;
  text-transform: capitalize;
}

.details-text {
  font-size: 13px;
  color: var(--text-secondary);
}
</style>
