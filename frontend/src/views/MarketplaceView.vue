<template>
  <div class="marketplace">
    <div class="page-header">
      <h2>Surge Capacity Marketplace</h2>
      <p class="page-subtitle">Share and discover available warehouse space, transport, and personnel</p>
    </div>

    <!-- Filter buttons -->
    <div class="filter-bar">
      <button
        v-for="f in filters"
        :key="f.value"
        class="filter-btn"
        :class="{ active: activeFilter === f.value }"
        @click="activeFilter = f.value"
      >
        {{ f.label }}
        <span class="filter-count">{{ countByType(f.value) }}</span>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Loading listings...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <p>Failed to load marketplace listings.</p>
      <button class="retry-btn" @click="fetchListings">Retry</button>
    </div>

    <!-- Empty -->
    <div v-else-if="!filteredListings.length" class="empty-state">
      <p>No listings found{{ activeFilter !== 'all' ? ' for this category' : '' }}.</p>
    </div>

    <!-- Listing cards grid -->
    <div v-else class="listings-grid">
      <div v-for="listing in filteredListings" :key="listing.id" class="listing-card">
        <div class="listing-header">
          <span class="type-badge" :class="typeClass(listing.listing_type)">
            {{ formatType(listing.listing_type) }}
          </span>
          <StatusBadge :status="listing.status" size="sm" />
        </div>
        <h3 class="listing-title">{{ listing.title }}</h3>
        <p class="listing-desc">{{ listing.description }}</p>
        <div class="listing-details">
          <div class="detail-row">
            <span class="detail-label">Capacity</span>
            <span class="detail-value">{{ listing.capacity_value?.toLocaleString() }} {{ listing.capacity_unit }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Location</span>
            <span class="detail-value">{{ listing.location }}</span>
          </div>
          <div v-if="listing.available_from" class="detail-row">
            <span class="detail-label">Available</span>
            <span class="detail-value">
              {{ formatDate(listing.available_from) }}
              <template v-if="listing.available_until"> &ndash; {{ formatDate(listing.available_until) }}</template>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Map -->
    <div v-if="!loading && mapMarkers.length" class="map-section">
      <h3 class="section-title">Listing Locations</h3>
      <div class="map-wrapper">
        <MapView :markers="mapMarkers" :center="[20, 30]" :zoom="2" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { marketplaceApi } from '../api/client'
import MapView from '../components/common/MapView.vue'
import StatusBadge from '../components/common/StatusBadge.vue'

const listings = ref([])
const loading = ref(true)
const error = ref(false)
const activeFilter = ref('all')

const filters = [
  { label: 'All', value: 'all' },
  { label: 'Warehouse Space', value: 'warehouse_space' },
  { label: 'Transport', value: 'transport' },
  { label: 'Personnel', value: 'personnel' }
]

const filteredListings = computed(() => {
  if (activeFilter.value === 'all') return listings.value
  return listings.value.filter(l => l.listing_type === activeFilter.value)
})

function countByType(type) {
  if (type === 'all') return listings.value.length
  return listings.value.filter(l => l.listing_type === type).length
}

function typeClass(type) {
  const map = {
    warehouse_space: 'type-warehouse',
    transport: 'type-transport',
    personnel: 'type-personnel'
  }
  return map[type] || 'type-warehouse'
}

function formatType(type) {
  return (type || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}

const mapMarkers = computed(() => {
  return filteredListings.value
    .filter(l => l.latitude != null && l.longitude != null)
    .map(l => ({
      lat: l.latitude,
      lng: l.longitude,
      label: l.title,
      popup: `<strong>${l.title}</strong><br/>${l.location}<br/>${l.capacity_value?.toLocaleString()} ${l.capacity_unit}`,
      color: l.listing_type === 'warehouse_space' ? 'blue' : l.listing_type === 'transport' ? 'orange' : 'green',
      radius: 10
    }))
})

async function fetchListings() {
  loading.value = true
  error.value = false
  try {
    const { data } = await marketplaceApi.list()
    listings.value = Array.isArray(data) ? data : data.listings || []
  } catch (e) {
    console.error('Failed to load marketplace:', e)
    error.value = true
  } finally {
    loading.value = false
  }
}

onMounted(fetchListings)
</script>

<style scoped>
.marketplace {
  max-width: 1200px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.filter-btn:hover {
  border-color: var(--primary);
  color: var(--text);
}

.filter-btn.active {
  background: var(--primary);
  border-color: var(--primary);
  color: #ffffff;
}

.filter-count {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.15);
}

.filter-btn:not(.active) .filter-count {
  background: var(--bg);
}

.listings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.listing-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px;
  transition: border-color 0.15s ease;
}

.listing-card:hover {
  border-color: var(--primary);
}

.listing-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.type-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 10px;
  text-transform: capitalize;
}

.type-warehouse {
  background: rgba(30, 58, 95, 0.12);
  color: var(--primary);
}

.type-transport {
  background: rgba(232, 145, 58, 0.12);
  color: var(--accent);
}

.type-personnel {
  background: rgba(39, 174, 96, 0.12);
  color: var(--success);
}

.listing-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
  line-height: 1.3;
}

.listing-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.listing-details {
  border-top: 1px solid var(--border);
  padding-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.detail-label {
  color: var(--text-secondary);
}

.detail-value {
  color: var(--text);
  font-weight: 500;
  text-align: right;
}

.map-section {
  margin-top: 8px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 12px;
}

.map-wrapper {
  height: 400px;
  border-radius: 8px;
  overflow: hidden;
}

.loading-state,
.empty-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  color: var(--text-secondary);
  gap: 12px;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.retry-btn {
  padding: 8px 20px;
  border: 1px solid var(--primary);
  border-radius: 6px;
  background: transparent;
  color: var(--primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.retry-btn:hover {
  background: var(--primary);
  color: #ffffff;
}

@media (max-width: 768px) {
  .listings-grid {
    grid-template-columns: 1fr;
  }
}
</style>
