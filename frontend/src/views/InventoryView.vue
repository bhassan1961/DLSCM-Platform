<template>
  <div class="inventory">
    <div class="inventory-layout">
      <!-- Warehouse List -->
      <div class="warehouse-panel">
        <div class="panel-header">
          <h3>Warehouses</h3>
        </div>
        <div v-if="warehousesLoading" class="loading-state">
          <div class="spinner"></div>
        </div>
        <div v-else-if="!warehouses.length" class="empty-state">No warehouses found</div>
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
          <h3>
            {{ selectedWarehouse ? selectedWarehouse.name + ' Stock' : 'Select a Warehouse' }}
          </h3>
          <select
            v-if="selectedWarehouse"
            v-model="categoryFilter"
            class="category-filter"
          >
            <option value="">All Categories</option>
            <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
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
        </DataTable>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import DataTable from '../components/common/DataTable.vue'
import { inventoryApi } from '../api/client'

const warehouses = ref([])
const warehousesLoading = ref(true)
const selectedWarehouse = ref(null)
const stock = ref([])
const stockLoading = ref(false)
const categoryFilter = ref('')
const editingId = ref(null)
const editQty = ref(0)

const stockColumns = [
  { key: 'item_name', label: 'Item', sortable: true },
  { key: 'sku', label: 'SKU', sortable: true },
  { key: 'category', label: 'Category', sortable: true },
  { key: 'quantity', label: 'Quantity', sortable: true, width: '120px' },
  { key: 'unit', label: 'Unit' },
  { key: 'lot_number', label: 'Lot#' },
  { key: 'expiry_date', label: 'Expiry', sortable: true }
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
    console.error('Failed to load stock:', e)
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
    console.error('Failed to update stock:', e)
  }
  editingId.value = null
}

onMounted(async () => {
  try {
    const { data } = await inventoryApi.warehouses()
    warehouses.value = data.warehouses || data || []
    if (warehouses.value.length) {
      selectWarehouse(warehouses.value[0])
    }
  } catch (e) {
    console.error('Failed to load warehouses:', e)
  } finally {
    warehousesLoading.value = false
  }
})
</script>

<style scoped>
.inventory-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 24px;
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
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  border-radius: 8px 8px 0 0;
}

.panel-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.category-filter {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--text);
  font-size: 13px;
}

.warehouse-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.warehouse-card {
  padding: 14px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: 4px;
}

.warehouse-card:hover {
  background: var(--bg);
}

.warehouse-card.active {
  background: var(--bg);
  border-left: 3px solid var(--primary);
  padding-left: 13px;
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
}

.qty-cell {
  display: flex;
  align-items: center;
}

.qty-value {
  cursor: pointer;
  padding: 2px 8px;
  border-radius: 4px;
  transition: background 0.15s ease;
}

.qty-value:hover {
  background: var(--bg);
}

.qty-input {
  width: 80px;
  padding: 4px 8px;
  border: 1px solid var(--primary);
  border-radius: 4px;
  background: var(--surface);
  color: var(--text);
  font-size: 14px;
}

.loading-state,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  color: var(--text-secondary);
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
