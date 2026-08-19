<template>
  <div class="inventory">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="error = null" />
    <div class="inventory-layout">
      <!-- Warehouse List -->
      <div class="warehouse-panel">
        <div class="panel-header">
          <h2 class="panel-title">{{ $t('inventory.warehouse') }}</h2>
        </div>
        <div v-if="warehousesLoading" class="loading-state">
          <div class="spinner"></div>
        </div>
        <div v-else-if="!warehouses.length" class="empty-state">{{ $t('common.noData') }}</div>
        <div v-else class="warehouse-list">
          <div
            v-for="wh in warehouses"
            :key="wh.id"
            class="warehouse-card"
            :class="{ active: selectedWarehouse?.id === wh.id }"
            @click="selectWarehouse(wh)"
          >
            <div class="wh-name">{{ wh.name }}</div>
            <div class="wh-location">{{ wh.location }}</div>
            <div class="wh-stock">{{ wh.stock_count ?? '?' }} items</div>
          </div>
        </div>
      </div>

      <!-- Stock Table -->
      <div class="stock-panel">
        <div class="panel-header">
          <h2 class="panel-title">
            {{ selectedWarehouse ? selectedWarehouse.name + ' Stock' : 'Select a Warehouse' }}
          </h2>
          <div class="panel-actions">
            <select
              v-if="selectedWarehouse"
              v-model="categoryFilter"
              class="category-filter"
            >
              <option value="">All Categories</option>
              <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
            <button v-if="selectedWarehouse" class="btn-primary" @click="showAddItem = true">+ {{ $t('inventory.addItem') }}</button>
          </div>
        </div>
        <DataTable
          :columns="stockColumns"
          :rows="filteredStock"
          :loading="stockLoading"
          @row-click="() => {}"
        >
          <template #cell-quantity="{ row }">
            <div class="qty-cell">
              <template v-if="editingId === row.id">
                <input
                  type="number"
                  v-model.number="editQty"
                  class="qty-input"
                  @keydown.enter="saveQuantity(row)"
                  @blur="saveQuantity(row)"
                  ref="qtyInputRef"
                />
              </template>
              <template v-else>
                <span class="qty-value" @click.stop="startEdit(row)">
                  {{ row.quantity }}
                </span>
              </template>
            </div>
          </template>
          <template #cell-expiry_date="{ value }">
            {{ value ? new Date(value).toLocaleDateString() : '-' }}
          </template>
          <template #cell-actions="{ row }">
            <button class="btn-icon-danger" @click.stop="deleteItem(row.item_id)" title="Delete item">&#10005;</button>
          </template>
        </DataTable>

    <!-- Add Item Modal -->
    <div v-if="showAddItem" class="modal-overlay" @click.self="showAddItem = false">
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="add-item-title" @keydown.escape="showAddItem = false">
        <div class="modal-header">
          <h3 id="add-item-title">{{ $t('inventory.addItem') }}</h3>
          <button class="modal-close" @click="showAddItem = false" aria-label="Close">&times;</button>
        </div>
        <form @submit.prevent="addItem" class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label for="inv-name">{{ $t('inventory.itemName') }}</label>
              <input id="inv-name" v-model="itemForm.name" required placeholder="e.g. Tarpaulin Sheet" />
            </div>
            <div class="form-group">
              <label for="inv-sku">{{ $t('inventory.sku') }}</label>
              <input id="inv-sku" v-model="itemForm.sku" required placeholder="e.g. TARP-001" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="inv-category">{{ $t('common.category') }}</label>
              <select id="inv-category" v-model="itemForm.category" required>
                <option value="food">{{ $t('common.food') }}</option>
                <option value="water">{{ $t('common.water') }}</option>
                <option value="medical">{{ $t('common.medical') }}</option>
                <option value="shelter">{{ $t('common.shelter') }}</option>
                <option value="hygiene">{{ $t('common.hygiene') }}</option>
                <option value="nfi">{{ $t('common.nfi') }}</option>
              </select>
            </div>
            <div class="form-group">
              <label for="inv-unit">{{ $t('inventory.unit') }}</label>
              <input id="inv-unit" v-model="itemForm.unit" required placeholder="e.g. pieces, kg, liters" />
            </div>
          </div>
          <div class="form-group">
            <label for="inv-min">{{ $t('inventory.minRequired') }}</label>
            <input id="inv-min" type="number" v-model.number="itemForm.minimum_stock" placeholder="e.g. 100" />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showAddItem = false">{{ $t('common.cancel') }}</button>
            <button type="submit" class="btn-primary" :disabled="addingItem">{{ addingItem ? $t('common.loading') : $t('inventory.addItem') }}</button>
          </div>
        </form>
      </div>
    </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import DataTable from '../components/common/DataTable.vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { inventoryApi } from '../api/client'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const warehouses = ref([])
const warehousesLoading = ref(true)
const selectedWarehouse = ref(null)
const stock = ref([])
const stockLoading = ref(false)
const categoryFilter = ref('')
const editingId = ref(null)
const editQty = ref(0)

const showAddItem = ref(false)
const addingItem = ref(false)
const itemForm = ref({ name: '', sku: '', category: 'food', unit: 'pieces', minimum_stock: 0 })

const stockColumns = [
  { key: 'item_name', label: 'Item', sortable: true },
  { key: 'sku', label: 'SKU', sortable: true },
  { key: 'category', label: 'Category', sortable: true },
  { key: 'quantity', label: 'Quantity', sortable: true, width: '120px' },
  { key: 'unit', label: 'Unit' },
  { key: 'lot_number', label: 'Lot#' },
  { key: 'expiry_date', label: 'Expiry', sortable: true },
  { key: 'actions', label: '', width: '50px' }
]

const categories = computed(() => {
  const cats = new Set(stock.value.map(s => s.category).filter(Boolean))
  return [...cats].sort()
})

const filteredStock = computed(() => {
  if (!categoryFilter.value) return stock.value
  return stock.value.filter(s => s.category === categoryFilter.value)
})

async function selectWarehouse(wh) {
  selectedWarehouse.value = wh
  stockLoading.value = true
  try {
    const { data } = await inventoryApi.warehouseStock(wh.id)
    const raw = data.stock || data || []
    stock.value = raw.map(s => ({
      id: s.id,
      warehouse_id: s.warehouse_id,
      item_id: s.item_id,
      item_name: s.item?.name || s.item_name || '',
      sku: s.item?.sku || s.sku || '',
      category: s.item?.category || s.category || '',
      unit: s.item?.unit || s.unit || '',
      quantity: s.quantity,
      lot_number: s.lot_number,
      expiry_date: s.expiry_date,
    }))
  } catch (e) {
    handleError(e, 'Failed to load stock')
    stock.value = []
  } finally {
    stockLoading.value = false
  }
}

function startEdit(row) {
  editingId.value = row.id
  editQty.value = row.quantity
  nextTick(() => {
    const input = document.querySelector('.qty-input')
    if (input) input.focus()
  })
}

async function saveQuantity(row) {
  if (editQty.value === row.quantity) {
    editingId.value = null
    return
  }
  try {
    await inventoryApi.updateStock(row.id, editQty.value)
    row.quantity = editQty.value
  } catch (e) {
    handleError(e, 'Failed to update stock')
  }
  editingId.value = null
}

async function addItem() {
  addingItem.value = true
  try {
    await inventoryApi.createItem(itemForm.value)
    showAddItem.value = false
    itemForm.value = { name: '', sku: '', category: 'food', unit: 'pieces', minimum_stock: 0 }
    if (selectedWarehouse.value) {
      await selectWarehouse(selectedWarehouse.value)
    }
  } catch (e) {
    handleError(e, 'Failed to add item')
  } finally {
    addingItem.value = false
  }
}

async function deleteItem(itemId) {
  try {
    await inventoryApi.deleteItem(itemId)
    stock.value = stock.value.filter(s => s.item_id !== itemId)
  } catch (e) {
    handleError(e, 'Failed to delete item')
  }
}

async function loadWarehouses() {
  warehousesLoading.value = true
  clearError()
  try {
    const { data } = await inventoryApi.warehouses()
    warehouses.value = data.warehouses || data || []
    if (warehouses.value.length) {
      selectWarehouse(warehouses.value[0])
    }
  } catch (e) {
    handleError(e, 'Failed to load warehouses')
  } finally {
    warehousesLoading.value = false
  }
}

function retryLoad() {
  clearError()
  loadWarehouses()
}

onMounted(loadWarehouses)
</script>

<style scoped>
.inventory-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
  height: calc(100vh - 108px);
}

@media (max-width: 900px) {
  .inventory-layout {
    grid-template-columns: 1fr;
    height: auto;
  }
}

.warehouse-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.stock-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  gap: 12px;
}

.panel-header .panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: 0.01em;
}

.category-filter {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: 13px;
  transition: border-color 0.15s ease;
}

.category-filter:focus {
  border-color: var(--accent);
}

.warehouse-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.warehouse-card {
  padding: 14px 16px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: 4px;
  border-left: 3px solid transparent;
}

.warehouse-card:hover {
  background: var(--bg);
}

.warehouse-card.active {
  background: var(--bg);
  border-left-color: var(--accent);
}

.wh-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text);
}

.wh-location {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.wh-stock {
  font-size: 12px;
  color: var(--accent);
  margin-top: 4px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.qty-cell {
  display: flex;
  align-items: center;
}

.qty-value {
  cursor: pointer;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  transition: background 0.15s ease;
  font-variant-numeric: tabular-nums;
}

.qty-value:hover {
  background: var(--bg);
}

.qty-input {
  width: 80px;
  padding: 4px 8px;
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: 14px;
  font-variant-numeric: tabular-nums;
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
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-primary {
  padding: 6px 14px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
  white-space: nowrap;
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
}
.btn-icon-danger:hover { opacity: 1; }

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
  max-width: 480px;
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
.form-group select {
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
  .form-row { flex-direction: column; }
}
</style>
