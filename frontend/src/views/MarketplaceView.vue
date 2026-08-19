<template>
  <div class="marketplace">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="page-header">
      <h2>{{ $t('marketplace.title') }}</h2>
      <p class="page-subtitle">{{ $t('marketplace.subtitle') }}</p>
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
      <span>{{ $t('marketplace.loadingListings') }}</span>
    </div>

    <!-- Empty -->
    <div v-else-if="!filteredListings.length" class="empty-state">
      <p>{{ activeFilter !== 'all' ? $t('marketplace.noListingsCategory') : $t('marketplace.noListings') }}</p>
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
            <span class="detail-label">{{ $t('marketplace.capacity') }}</span>
            <span class="detail-value">{{ listing.capacity_value?.toLocaleString() }} {{ listing.capacity_unit }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ $t('marketplace.location') }}</span>
            <span class="detail-value">{{ listing.location }}</span>
          </div>
          <div v-if="listing.available_from" class="detail-row">
            <span class="detail-label">{{ $t('marketplace.available') }}</span>
            <span class="detail-value">
              {{ formatDate(listing.available_from) }}
              <template v-if="listing.available_until"> &ndash; {{ formatDate(listing.available_until) }}</template>
            </span>
          </div>
        </div>
        <div class="listing-actions">
          <button v-if="listing.status === 'available'" class="book-btn" @click="openBooking(listing)">{{ $t('marketplace.book') }}</button>
          <button class="match-btn" @click="findMatches(listing)">{{ $t('marketplace.findMatches') }}</button>
        </div>
      </div>
    </div>

    <!-- Matches panel -->
    <div v-if="matchResult" class="matches-panel">
      <div class="matches-header">
        <h3 class="section-title">{{ $t('marketplace.topMatches') }}</h3>
        <button class="close-btn" @click="matchResult = null">&times;</button>
      </div>
      <div v-for="m in matchResult.matches" :key="m.id" class="match-row">
        <div class="match-info">
          <span class="match-title">{{ m.title }}</span>
          <span class="match-meta">{{ m.location }} &middot; {{ m.capacity_value?.toLocaleString() }} {{ m.capacity_unit }}</span>
        </div>
        <div class="match-score" :style="{ '--score': m.score }">{{ (m.score * 100).toFixed(0) }}%</div>
      </div>
      <p v-if="!matchResult.matches?.length" class="no-matches">{{ $t('marketplace.noMatches') }}</p>
    </div>

    <!-- Booking modal -->
    <div v-if="bookingListing" class="modal-overlay" @click.self="bookingListing = null">
      <div class="modal-card">
        <h3>{{ $t('marketplace.bookTitle', { title: bookingListing.title }) }}</h3>
        <form @submit.prevent="submitBooking" class="form-stack">
          <div class="form-group">
            <label class="form-label">{{ $t('marketplace.yourOrganization') }}</label>
            <input v-model="bookForm.requester_org" class="form-input" :placeholder="$t('marketplace.orgPlaceholder')" required />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('marketplace.quantityNeeded') }}</label>
            <input v-model.number="bookForm.quantity_needed" class="form-input" type="number" min="1" required />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('common.notes') }}</label>
            <textarea v-model="bookForm.notes" class="form-input" rows="2" :placeholder="$t('common.optional')"></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="bookingListing = null">{{ $t('common.cancel') }}</button>
            <button type="submit" class="action-btn" :disabled="bookingInProgress">{{ bookingInProgress ? $t('marketplace.booking') : $t('marketplace.confirmBooking') }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Bookings section -->
    <div v-if="bookings.length" class="bookings-section">
      <h3 class="section-title">{{ $t('marketplace.yourBookings') }}</h3>
      <div v-for="b in bookings" :key="b.id" class="booking-row">
        <div class="booking-info">
          <span class="booking-title">{{ b.listing_title }}</span>
          <span class="booking-meta">{{ b.location }} &middot; {{ b.requester_org }}</span>
        </div>
        <StatusBadge :status="b.status" size="sm" />
        <button v-if="b.status === 'confirmed'" class="cancel-btn" @click="cancelBooking(b.id)">{{ $t('common.cancel') }}</button>
      </div>
    </div>

    <!-- Map -->
    <div v-if="!loading && mapMarkers.length" class="map-section">
      <h3 class="section-title">{{ $t('marketplace.listingLocations') }}</h3>
      <div class="map-wrapper">
        <MapView :markers="mapMarkers" :center="[20, 30]" :zoom="2" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { marketplaceApi } from '../api/client'
import MapView from '../components/common/MapView.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { useErrorHandler } from '../composables/useErrorHandler'

const { t } = useI18n()

const { error, handleError, clearError } = useErrorHandler()

const listings = ref([])
const loading = ref(true)
const activeFilter = ref('all')
const matchResult = ref(null)
const bookingListing = ref(null)
const bookingInProgress = ref(false)
const bookings = ref([])
const bookForm = reactive({ requester_org: '', quantity_needed: 1, notes: '' })

const filters = computed(() => [
  { label: t('common.all'), value: 'all' },
  { label: t('marketplace.warehouseSpace'), value: 'warehouse_space' },
  { label: t('marketplace.transport'), value: 'transport' },
  { label: t('marketplace.personnel'), value: 'personnel' }
])

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

function openBooking(listing) {
  bookingListing.value = listing
  Object.assign(bookForm, { requester_org: '', quantity_needed: 1, notes: '' })
}

async function findMatches(listing) {
  try {
    const { data } = await marketplaceApi.match(listing.id)
    matchResult.value = data
  } catch (e) { handleError(e, 'Failed to find matches') }
}

async function submitBooking() {
  bookingInProgress.value = true
  try {
    await marketplaceApi.book(bookingListing.value.id, bookForm)
    bookingListing.value = null
    await fetchListings()
    await fetchBookings()
  } catch (e) { handleError(e, 'Failed to submit booking') }
  finally { bookingInProgress.value = false }
}

async function cancelBooking(id) {
  try {
    await marketplaceApi.cancelBooking(id)
    await fetchListings()
    await fetchBookings()
  } catch (e) { handleError(e, 'Failed to cancel booking') }
}

async function fetchBookings() {
  try {
    const { data } = await marketplaceApi.bookings()
    bookings.value = Array.isArray(data) ? data : []
  } catch (e) { handleError(e, 'Failed to load bookings') }
}

async function fetchListings() {
  loading.value = true
  clearError()
  try {
    const { data } = await marketplaceApi.list()
    listings.value = Array.isArray(data) ? data : data.listings || []
  } catch (e) {
    handleError(e, 'Failed to load marketplace')
  } finally {
    loading.value = false
  }
}

function retryLoad() {
  clearError()
  fetchListings()
  fetchBookings()
}

onMounted(() => { fetchListings(); fetchBookings() })
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
  border-radius: var(--radius);
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
  border-radius: var(--radius);
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
  border-radius: var(--radius);
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
  border-radius: var(--radius);
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
  border-radius: var(--radius);
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
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.retry-btn {
  padding: 8px 20px;
  border: 1px solid var(--primary);
  border-radius: var(--radius-sm);
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

.listing-actions { display: flex; gap: 8px; margin-top: 12px; border-top: 1px solid var(--border); padding-top: 12px; }
.book-btn { flex: 1; padding: 8px; border: none; border-radius: var(--radius-sm); background: var(--primary); color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; }
.book-btn:hover { filter: brightness(1.1); }
.match-btn { flex: 1; padding: 8px; border: 1px solid var(--primary); border-radius: var(--radius-sm); background: transparent; color: var(--primary); font-size: 13px; font-weight: 600; cursor: pointer; }
.match-btn:hover { background: var(--primary); color: #fff; }

.matches-panel { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 24px; }
.matches-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.close-btn { background: none; border: none; color: var(--text-secondary); font-size: 20px; cursor: pointer; padding: 0 4px; }
.match-row { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--border); }
.match-row:last-child { border-bottom: none; }
.match-info { flex: 1; }
.match-title { display: block; font-size: 14px; font-weight: 600; color: var(--text); }
.match-meta { display: block; font-size: 12px; color: var(--text-secondary); }
.match-score { font-size: 14px; font-weight: 700; color: var(--success); }
.no-matches { font-size: 13px; color: var(--text-secondary); }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-card { background: var(--surface); border-radius: var(--radius); padding: 28px; width: 90vw; max-width: 440px; }
.modal-card h3 { font-size: 18px; font-weight: 600; color: var(--text); margin-bottom: 20px; }
.form-stack { display: flex; flex-direction: column; gap: 14px; }
.form-group { display: flex; flex-direction: column; }
.form-label { font-size: 12px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.form-input { padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); color: var(--text); font-size: 14px; }
.form-input:focus { outline: none; border-color: var(--primary); }
textarea.form-input { resize: vertical; font-family: inherit; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }
.btn-secondary { padding: 8px 20px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: transparent; color: var(--text-secondary); font-size: 14px; cursor: pointer; }
.action-btn { padding: 8px 20px; border: none; border-radius: var(--radius-sm); background: var(--primary); color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; }
.action-btn:hover:not(:disabled) { filter: brightness(1.1); }
.action-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.bookings-section { margin-bottom: 24px; }
.booking-row { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); margin-bottom: 8px; }
.booking-info { flex: 1; }
.booking-title { display: block; font-size: 14px; font-weight: 600; color: var(--text); }
.booking-meta { display: block; font-size: 12px; color: var(--text-secondary); }
.cancel-btn { padding: 4px 12px; border: 1px solid var(--danger); border-radius: var(--radius-sm); background: transparent; color: var(--danger); font-size: 12px; cursor: pointer; }
.cancel-btn:hover { background: var(--danger); color: #fff; }

@media (max-width: 768px) {
  .listings-grid {
    grid-template-columns: 1fr;
  }
}
</style>
