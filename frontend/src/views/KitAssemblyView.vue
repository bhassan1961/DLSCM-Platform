<template>
  <div class="kits-view">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="page-header">
      <div>
        <h2>{{ $t('kits.title') }}</h2>
        <p class="subtitle">{{ $t('kits.subtitle') }}</p>
      </div>
      <button class="action-btn" @click="showForm = !showForm">
        {{ showForm ? $t('common.cancel') : $t('kits.createKit') }}
      </button>
    </div>

    <!-- Create Kit Form -->
    <div v-if="showForm" class="form-panel">
      <h3>{{ $t('kits.newKit') }}</h3>
      <form @submit.prevent="submitKit">
        <div class="form-grid">
          <div class="form-group">
            <label for="kit-name">{{ $t('kits.kitName') }}</label>
            <input id="kit-name" v-model="form.name" required :placeholder="$t('kits.kitNamePlaceholder')" />
          </div>
          <div class="form-group">
            <label for="kit-category">{{ $t('common.category') }}</label>
            <select id="kit-category" v-model="form.category" required>
              <option value="">{{ $t('kits.selectCategory') }}</option>
              <option value="hygiene">{{ $t('kits.hygiene') }}</option>
              <option value="medical">{{ $t('kits.medical') }}</option>
              <option value="shelter">{{ $t('kits.shelter') }}</option>
              <option value="food">{{ $t('kits.food') }}</option>
              <option value="water">{{ $t('kits.water') }}</option>
              <option value="nfi">{{ $t('kits.nfi') }}</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label for="kit-description">{{ $t('common.description') }}</label>
          <textarea id="kit-description" v-model="form.description" rows="2" :placeholder="$t('kits.kitDescriptionPlaceholder')"></textarea>
        </div>
        <div class="form-group">
          <label>{{ $t('kits.components') }}</label>
          <div v-for="(comp, i) in form.components" :key="i" class="component-row">
            <select v-model="comp.item_id" class="comp-select">
              <option value="">{{ $t('kits.selectItem') }}</option>
              <option v-for="item in availableItems" :key="item.id" :value="item.id">
                {{ item.name }}
              </option>
            </select>
            <input v-model.number="comp.quantity" type="number" min="1" :placeholder="$t('kits.qty')" class="comp-qty" />
            <button type="button" class="remove-btn" @click="form.components.splice(i, 1)">&times;</button>
          </div>
          <button type="button" class="add-component-btn" @click="form.components.push({ item_id: '', quantity: 1 })">
            {{ $t('kits.addComponent') }}
          </button>
        </div>
        <div class="form-actions">
          <button type="button" class="cancel-btn" @click="showForm = false">{{ $t('common.cancel') }}</button>
          <button type="submit" class="submit-btn" :disabled="submitting">
            {{ submitting ? $t('kits.creating') : $t('kits.createKitAction') }}
          </button>
        </div>
      </form>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>{{ $t('kits.loadingKits') }}</span>
    </div>

    <!-- Empty state -->
    <div v-else-if="!kits.length" class="empty-state">
      <p>{{ $t('kits.emptyState') }}</p>
    </div>

    <!-- Kit Cards Grid -->
    <div v-else class="kits-grid">
      <div v-for="kit in kits" :key="kit.id" class="kit-card" @click="toggleExpand(kit.id)">
        <div class="kit-header">
          <h4>{{ kit.name }}</h4>
          <span class="category-badge">{{ kit.category }}</span>
        </div>
        <p class="kit-description" v-if="kit.description">{{ kit.description }}</p>
        <div class="kit-meta">
          <span class="component-count">{{ (kit.components || []).length }} {{ $t('kits.components') }}</span>
          <span class="expand-icon">{{ expandedId === kit.id ? '▲' : '▼' }}</span>
        </div>
        <div v-if="expandedId === kit.id && kit.components?.length" class="component-list">
          <div v-for="(comp, i) in kit.components" :key="i" class="component-item">
            <span class="comp-name">{{ comp.item_name || comp.name || $t('kits.itemNumber', { id: comp.item_id }) }}</span>
            <span class="comp-qty-label">x{{ comp.quantity }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { kitsApi, inventoryApi } from '../api/client'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const kits = ref([])
const availableItems = ref([])
const loading = ref(true)
const showForm = ref(false)
const submitting = ref(false)
const expandedId = ref(null)

const form = ref({
  name: '', description: '', category: '',
  components: [{ item_id: '', quantity: 1 }]
})

function toggleExpand(id) {
  expandedId.value = expandedId.value === id ? null : id
}

async function submitKit() {
  submitting.value = true
  try {
    const payload = {
      ...form.value,
      components: form.value.components.filter(c => c.item_id)
    }
    await kitsApi.create(payload)
    showForm.value = false
    form.value = { name: '', description: '', category: '', components: [{ item_id: '', quantity: 1 }] }
    await loadKits()
  } catch (e) {
    handleError(e, 'Failed to create kit')
  } finally {
    submitting.value = false
  }
}

async function loadKits() {
  loading.value = true
  try {
    const { data } = await kitsApi.list()
    kits.value = data.kits || data || []
  } catch (e) {
    handleError(e, 'Failed to load kits')
  } finally {
    loading.value = false
  }
}

function retryLoad() {
  clearError()
  loadKits()
}

onMounted(async () => {
  const results = await Promise.allSettled([
    kitsApi.list(),
    inventoryApi.items()
  ])
  if (results[0].status === 'fulfilled') {
    const d = results[0].value.data
    kits.value = d.kits || d || []
  }
  if (results[1].status === 'fulfilled') {
    const d = results[1].value.data
    availableItems.value = d.items || d || []
  }
  loading.value = false
})
</script>

<style scoped>
.kits-view {
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

.component-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.comp-select { flex: 1; }

.comp-qty {
  width: 80px;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
}

.remove-btn {
  background: none;
  border: none;
  color: var(--danger);
  font-size: 18px;
  padding: 0 4px;
  cursor: pointer;
}

.add-component-btn {
  background: none;
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  width: 100%;
  cursor: pointer;
}

.add-component-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
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

.submit-btn:disabled { opacity: 0.6; }

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px;
  color: var(--text-secondary);
  gap: 12px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  text-align: center;
  padding: 48px;
  color: var(--text-secondary);
  font-size: 14px;
}

.kits-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.kit-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  cursor: pointer;
  transition: border-color 0.15s ease;
}

.kit-card:hover {
  border-color: var(--primary);
}

.kit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.kit-header h4 {
  font-size: 16px;
  color: var(--text);
  margin: 0;
}

.category-badge {
  padding: 2px 10px;
  border-radius: var(--radius);
  font-size: 11px;
  font-weight: 600;
  background: rgba(30, 58, 95, 0.12);
  color: var(--primary);
  text-transform: capitalize;
}

.kit-description {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 12px;
}

.kit-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-secondary);
}

.expand-icon {
  font-size: 10px;
}

.component-list {
  margin-top: 12px;
  border-top: 1px solid var(--border);
  padding-top: 12px;
}

.component-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  margin-bottom: 4px;
  font-size: 14px;
  color: var(--text);
}

.comp-qty-label {
  font-weight: 600;
  color: var(--accent);
}
</style>
