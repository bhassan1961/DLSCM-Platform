<template>
  <div class="suppliers-view">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="page-header">
      <div>
        <h2>{{ $t('suppliers.title') }}</h2>
        <p class="subtitle">{{ $t('suppliers.subtitle') }}</p>
      </div>
      <button class="action-btn" @click="showForm = !showForm">
        {{ showForm ? $t('common.cancel') : $t('suppliers.addSupplier') }}
      </button>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <label for="sup-filter-cat" class="sr-only">{{ $t('suppliers.filterByCategory') }}</label>
      <select id="sup-filter-cat" v-model="selectedCategory" class="filter-select" @change="loadSuppliers">
        <option value="">{{ $t('suppliers.allCategories') }}</option>
        <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
      </select>
    </div>

    <!-- Inline Form Panel -->
    <div v-if="showForm" class="form-panel">
      <h3>{{ $t('suppliers.newSupplier') }}</h3>
      <form @submit.prevent="submitSupplier">
        <div class="form-grid">
          <div class="form-group">
            <label for="sup-name">{{ $t('common.name') }}</label>
            <input id="sup-name" v-model="form.name" required :placeholder="$t('suppliers.supplierNamePlaceholder')" />
          </div>
          <div class="form-group">
            <label for="sup-category">{{ $t('common.category') }}</label>
            <select id="sup-category" v-model="form.category" required>
              <option value="">{{ $t('suppliers.selectCategory') }}</option>
              <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>
          <div class="form-group">
            <label for="sup-country">{{ $t('common.country') }}</label>
            <input id="sup-country" v-model="form.country" :placeholder="$t('common.country')" />
          </div>
          <div class="form-group">
            <label for="sup-email">{{ $t('suppliers.contactEmail') }}</label>
            <input id="sup-email" v-model="form.contact_email" type="email" :placeholder="$t('suppliers.emailPlaceholder')" />
          </div>
          <div class="form-group">
            <label for="sup-lead-time">{{ $t('suppliers.leadTimeDays') }}</label>
            <input id="sup-lead-time" v-model.number="form.lead_time_days" type="number" min="0" :placeholder="$t('suppliers.daysPlaceholder')" />
          </div>
          <div class="form-group">
            <label for="sup-rating">{{ $t('suppliers.qualityRating') }}</label>
            <select id="sup-rating" v-model.number="form.quality_rating">
              <option :value="1">1</option>
              <option :value="2">2</option>
              <option :value="3">3</option>
              <option :value="4">4</option>
              <option :value="5">5</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label for="sup-capacity">{{ $t('suppliers.capacityDescription') }}</label>
          <input id="sup-capacity" v-model="form.capacity_description" :placeholder="$t('suppliers.capacityPlaceholder')" />
        </div>
        <div class="form-group checkbox-group">
          <label>
            <input type="checkbox" v-model="form.pre_qualified" />
            {{ $t('suppliers.preQualified') }}
          </label>
        </div>
        <div class="form-group">
          <label for="sup-notes">{{ $t('common.notes') }}</label>
          <textarea id="sup-notes" v-model="form.notes" rows="3" :placeholder="$t('suppliers.additionalNotesPlaceholder')"></textarea>
        </div>
        <div class="form-actions">
          <button type="button" class="cancel-btn" @click="showForm = false">{{ $t('common.cancel') }}</button>
          <button type="submit" class="submit-btn" :disabled="submitting">
            {{ submitting ? $t('common.saving') : $t('suppliers.addSupplier') }}
          </button>
        </div>
      </form>
    </div>

    <!-- Suppliers Table -->
    <DataTable :columns="columns" :rows="suppliers" :loading="loading">
      <template #cell-quality_rating="{ value }">
        <span class="rating">{{ renderStars(value) }} <span class="rating-num">{{ value }}/5</span></span>
      </template>
      <template #cell-pre_qualified="{ value }">
        <span class="badge" :class="value ? 'badge-success' : 'badge-default'">
          {{ value ? $t('common.yes') : $t('common.no') }}
        </span>
      </template>
      <template #cell-lead_time_days="{ value }">
        {{ value != null ? value + 'd' : '-' }}
      </template>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DataTable from '../components/common/DataTable.vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { suppliersApi } from '../api/client'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const categories = ['food', 'medical', 'shelter', 'logistics', 'water', 'nfi', 'general']

const columns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'category', label: 'Category', sortable: true, width: '120px' },
  { key: 'country', label: 'Country', sortable: true, width: '120px' },
  { key: 'lead_time_days', label: 'Lead Time', sortable: true, width: '100px' },
  { key: 'quality_rating', label: 'Quality Rating', sortable: true, width: '140px' },
  { key: 'pre_qualified', label: 'Pre-Qualified', sortable: true, width: '120px' },
  { key: 'contact_email', label: 'Contact', width: '200px' }
]

const suppliers = ref([])
const loading = ref(true)
const selectedCategory = ref('')
const showForm = ref(false)
const submitting = ref(false)

const form = ref({
  name: '', category: '', country: '', contact_email: '',
  lead_time_days: null, quality_rating: 3, capacity_description: '',
  pre_qualified: false, notes: ''
})

function renderStars(rating) {
  const n = Number(rating) || 0
  return '★'.repeat(n) + '☆'.repeat(5 - n)
}

async function loadSuppliers() {
  loading.value = true
  try {
    const { data } = await suppliersApi.list(selectedCategory.value || undefined)
    suppliers.value = data.suppliers || data || []
  } catch (e) {
    handleError(e, 'Failed to load suppliers')
  } finally {
    loading.value = false
  }
}

async function submitSupplier() {
  submitting.value = true
  try {
    await suppliersApi.create(form.value)
    showForm.value = false
    form.value = {
      name: '', category: '', country: '', contact_email: '',
      lead_time_days: null, quality_rating: 3, capacity_description: '',
      pre_qualified: false, notes: ''
    }
    await loadSuppliers()
  } catch (e) {
    handleError(e, 'Failed to create supplier')
  } finally {
    submitting.value = false
  }
}

function retryLoad() {
  clearError()
  loadSuppliers()
}

onMounted(() => {
  loadSuppliers()
})
</script>

<style scoped>
.suppliers-view {
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

.action-btn:hover {
  opacity: 0.9;
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
  min-width: 180px;
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

.form-group textarea {
  resize: vertical;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.checkbox-group input[type="checkbox"] {
  width: auto;
}

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

.submit-btn:disabled {
  opacity: 0.6;
}

.rating {
  font-size: 14px;
  color: var(--warning);
}

.rating-num {
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: 4px;
}

.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--radius);
  font-size: 12px;
  font-weight: 600;
}

.badge-success {
  background: rgba(39, 174, 96, 0.12);
  color: var(--success);
}

.badge-default {
  background: rgba(127, 127, 127, 0.12);
  color: var(--text-secondary);
}
</style>
