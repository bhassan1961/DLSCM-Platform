<template>
  <div class="data-table-wrapper">
    <div v-if="loading" class="table-loading">
      <div class="spinner"></div>
      <span>Loading...</span>
    </div>
    <div v-else-if="!rows.length" class="table-empty">
      <span class="empty-icon">&#x1F4CB;</span>
      <p>No data available</p>
    </div>
    <div v-else class="table-scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              :style="col.width ? { width: col.width } : {}"
              :class="{ sortable: col.sortable, sorted: sortKey === col.key }"
              @click="col.sortable && toggleSort(col.key)"
            >
              {{ col.label }}
              <span v-if="col.sortable && sortKey === col.key" class="sort-arrow">
                {{ sortDir === 'asc' ? '&#x25B2;' : '&#x25BC;' }}
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, idx) in sortedRows"
            :key="idx"
            class="table-row"
            @click="$emit('row-click', row, idx)"
          >
            <td v-for="col in columns" :key="col.key">
              <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
                {{ row[col.key] ?? '-' }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

defineEmits(['row-click'])

const sortKey = ref(null)
const sortDir = ref('asc')

function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}

const sortedRows = computed(() => {
  if (!sortKey.value) return props.rows
  const dir = sortDir.value === 'asc' ? 1 : -1
  return [...props.rows].sort((a, b) => {
    const va = a[sortKey.value]
    const vb = b[sortKey.value]
    if (va == null) return 1
    if (vb == null) return -1
    if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir
    return String(va).localeCompare(String(vb)) * dir
  })
})
</script>

<style scoped>
.data-table-wrapper {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.table-scroll {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
  background: var(--bg);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
  user-select: none;
}

.data-table th.sortable {
  cursor: pointer;
}

.data-table th.sortable:hover {
  color: var(--text);
}

.sort-arrow {
  font-size: 10px;
  margin-left: 4px;
}

.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  color: var(--text);
}

.table-row {
  cursor: pointer;
  transition: background 0.1s ease;
}

.table-row:hover {
  background: var(--bg);
}

.table-row:last-child td {
  border-bottom: none;
}

.table-loading,
.table-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  color: var(--text-secondary);
  gap: 12px;
}

.empty-icon {
  font-size: 32px;
  opacity: 0.5;
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
