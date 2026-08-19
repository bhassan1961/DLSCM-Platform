<template>
  <div class="cross-org">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="page-header">
      <h2>{{ $t('crossOrg.title') }}</h2>
      <p class="subtitle">{{ $t('crossOrg.subtitle') }}</p>
    </div>

    <!-- Summary Cards -->
    <div class="summary-cards">
      <div class="summary-card">
        <div class="card-value">{{ totalOrgs }}</div>
        <div class="card-label">{{ $t('crossOrg.organizations') }}</div>
      </div>
      <div class="summary-card">
        <div class="card-value">{{ totalItems }}</div>
        <div class="card-label">{{ $t('crossOrg.totalItems') }}</div>
      </div>
      <div class="summary-card">
        <div class="card-value">{{ totalQuantity.toLocaleString() }}</div>
        <div class="card-label">{{ $t('crossOrg.totalQuantity') }}</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <select v-model="orgFilter" class="filter-select">
        <option value="">{{ $t('crossOrg.allOrganizations') }}</option>
        <option v-for="org in organizations" :key="org" :value="org">{{ org }}</option>
      </select>
      <select v-model="categoryFilter" class="filter-select">
        <option value="">{{ $t('crossOrg.allCategories') }}</option>
        <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
      </select>
    </div>

    <!-- Data Table -->
    <DataTable
      :columns="columns"
      :rows="filteredRows"
      :loading="loading"
      @row-click="() => {}"
    >
      <template #cell-organization="{ row }">
        <span class="org-badge" :style="{ borderLeftColor: orgColor(row.organization) }">
          {{ row.organization }}
        </span>
      </template>
      <template #cell-quantity="{ value }">
        <span class="qty-badge">{{ value?.toLocaleString() }}</span>
      </template>
      <template #cell-expiry_date="{ value }">
        {{ value ? new Date(value).toLocaleDateString() : '-' }}
      </template>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import DataTable from '../components/common/DataTable.vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { inventoryApi } from '../api/client'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const stockData = ref([])
const loading = ref(true)
const orgFilter = ref('')
const categoryFilter = ref('')

const columns = [
  { key: 'organization', label: 'Organization', sortable: true },
  { key: 'warehouse', label: 'Warehouse', sortable: true },
  { key: 'item_name', label: 'Item', sortable: true },
  { key: 'category', label: 'Category', sortable: true },
  { key: 'sku', label: 'SKU', sortable: true },
  { key: 'quantity', label: 'Quantity', sortable: true, width: '110px' },
  { key: 'unit', label: 'Unit' },
  { key: 'lot_number', label: 'Lot#' },
  { key: 'expiry_date', label: 'Expiry', sortable: true }
]

const organizations = computed(() => {
  const orgs = new Set(stockData.value.map(r => r.organization))
  return [...orgs].sort()
})

const categories = computed(() => {
  const cats = new Set(stockData.value.map(r => r.category).filter(Boolean))
  return [...cats].sort()
})

const filteredRows = computed(() => {
  let rows = stockData.value
  if (orgFilter.value) {
    rows = rows.filter(r => r.organization === orgFilter.value)
  }
  if (categoryFilter.value) {
    rows = rows.filter(r => r.category === categoryFilter.value)
  }
  return rows
})

const totalOrgs = computed(() => {
  const orgs = new Set(filteredRows.value.map(r => r.organization))
  return orgs.size
})

const totalItems = computed(() => filteredRows.value.length)

const totalQuantity = computed(() =>
  filteredRows.value.reduce((sum, r) => sum + (r.quantity || 0), 0)
)

const orgColors = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
  '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'
]

function orgColor(name) {
  const idx = organizations.value.indexOf(name)
  return orgColors[idx % orgColors.length]
}

async function loadCrossOrgStock() {
  loading.value = true
  clearError()
  try {
    const { data } = await inventoryApi.crossOrg()
    stockData.value = Array.isArray(data) ? data : data.stock || []
  } catch (e) {
    handleError(e, 'Failed to load cross-org stock')
    stockData.value = []
  } finally {
    loading.value = false
  }
}

function retryLoad() {
  clearError()
  loadCrossOrgStock()
}

onMounted(loadCrossOrgStock)
</script>

<style scoped>
.cross-org {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  margin: 0;
}

.subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 4px 0 0;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 700px) {
  .summary-cards {
    grid-template-columns: 1fr;
  }
}

.summary-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
}

.card-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
}

.card-label {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 4px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-select {
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: 13px;
  min-width: 180px;
}

.org-badge {
  border-left: 3px solid;
  padding-left: 8px;
  font-weight: 500;
}

.qty-badge {
  font-weight: 600;
  color: var(--accent, var(--text));
}
</style>
