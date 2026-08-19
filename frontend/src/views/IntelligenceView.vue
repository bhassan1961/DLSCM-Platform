<template>
  <div class="intelligence">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="page-header">
      <div>
        <h2>{{ $t('intelligence.title') }}</h2>
        <p class="subtitle">{{ $t('intelligence.subtitle') }}</p>
      </div>
    </div>

    <!-- Crisis Selector -->
    <div class="controls-bar">
      <div class="control-group">
        <label class="control-label">{{ $t('intelligence.crisis') }}</label>
        <select v-model="selectedDisasterId" class="control-select" @change="onDisasterChange">
          <option :value="null" disabled>{{ $t('intelligence.selectCrisis') }}</option>
          <option v-for="d in disasters" :key="d.disaster_id" :value="d.disaster_id">
            {{ d.disaster_name }} — {{ d.country }} ({{ d.severity }})
          </option>
        </select>
      </div>
      <div class="control-group">
        <label class="control-label">{{ $t('intelligence.timeframe') }}</label>
        <select v-model="daysBack" class="control-select" @change="loadIntelligence">
          <option :value="30">{{ $t('intelligence.last30Days') }}</option>
          <option :value="90">{{ $t('intelligence.last90Days') }}</option>
          <option :value="180">{{ $t('intelligence.last6Months') }}</option>
          <option :value="365">{{ $t('intelligence.lastYear') }}</option>
        </select>
      </div>
      <div class="control-group">
        <label class="control-label">{{ $t('common.category') }}</label>
        <select v-model="categoryFilter" class="control-select">
          <option value="">{{ $t('intelligence.allCategories') }}</option>
          <option v-for="cat in availableCategories" :key="cat" :value="cat">{{ formatCategory(cat) }}</option>
        </select>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>{{ $t('intelligence.fetching') }}</span>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && !selectedDisaster" class="empty-state">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" /></svg>
      <h3>{{ $t('intelligence.selectCrisisPrompt') }}</h3>
      <p>{{ $t('intelligence.selectCrisisDescription') }}</p>
    </div>

    <!-- Results -->
    <div v-if="!loading && intel" class="intel-layout">
      <!-- Stats sidebar -->
      <div class="intel-sidebar">
        <div class="stats-card">
          <div class="stats-title">{{ $t('intelligence.summary') }}</div>
          <div class="stat-row">
            <span class="stat-label">{{ $t('intelligence.totalItems') }}</span>
            <span class="stat-value">{{ intel.total_items }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">{{ $t('intelligence.sources') }}</span>
            <span class="stat-value">{{ Object.keys(intel.source_breakdown).length }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">{{ $t('intelligence.fetched') }}</span>
            <span class="stat-value">{{ formatTime(intel.fetched_at) }}</span>
          </div>
        </div>

        <div class="stats-card">
          <div class="stats-title">{{ $t('intelligence.bySource') }}</div>
          <div v-for="(count, source) in intel.source_breakdown" :key="source" class="stat-row clickable" @click="sourceFilter = sourceFilter === source ? '' : source">
            <span class="stat-label" :class="{ active: sourceFilter === source }">{{ source }}</span>
            <span class="stat-count">{{ count }}</span>
          </div>
        </div>

        <div class="stats-card">
          <div class="stats-title">{{ $t('intelligence.byCategory') }}</div>
          <div v-for="(count, cat) in intel.categories" :key="cat" class="stat-row clickable" @click="categoryFilter = categoryFilter === cat ? '' : cat">
            <span class="stat-label" :class="{ active: categoryFilter === cat }">
              <span class="cat-dot" :style="{ background: categoryColor(cat) }"></span>
              {{ formatCategory(cat) }}
            </span>
            <span class="stat-count">{{ count }}</span>
          </div>
        </div>

        <div class="stats-card crisis-info">
          <div class="stats-title">{{ $t('intelligence.crisisDetails') }}</div>
          <div class="stat-row">
            <span class="stat-label">{{ $t('common.type') }}</span>
            <span class="stat-value type-badge">{{ selectedDisaster?.disaster_type }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">{{ $t('common.severity') }}</span>
            <span class="stat-value" :class="'sev-' + selectedDisaster?.severity">{{ selectedDisaster?.severity }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">{{ $t('intelligence.affected') }}</span>
            <span class="stat-value">{{ formatPop(selectedDisaster?.affected_population) }}</span>
          </div>
        </div>
      </div>

      <!-- Feed -->
      <div class="intel-feed">
        <div v-if="!filteredItems.length" class="empty-state small">
          <p>{{ $t('intelligence.noResults') }}</p>
        </div>

        <div v-for="item in filteredItems" :key="item.id" class="intel-item" :class="'cat-' + item.category">
          <div class="item-header">
            <div class="item-meta">
              <span class="cat-badge" :style="{ background: categoryColor(item.category) }">{{ formatCategory(item.category) }}</span>
              <span class="source-badge">{{ item.source_org }}</span>
              <span v-if="item.alert_level" class="alert-badge" :class="'alert-' + item.alert_level?.toLowerCase()">{{ item.alert_level }}</span>
            </div>
            <span class="item-date">{{ formatDate(item.published_at) }}</span>
          </div>
          <h4 class="item-title">
            <a v-if="item.url" :href="item.url" target="_blank" rel="noopener">{{ item.title }}</a>
            <span v-else>{{ item.title }}</span>
          </h4>
          <p class="item-summary">{{ item.summary }}</p>
          <div class="item-footer">
            <div class="item-tags">
              <span v-for="c in item.countries" :key="c" class="tag">{{ c }}</span>
              <span v-for="dt in item.disaster_types" :key="dt" class="tag type-tag">{{ dt }}</span>
            </div>
            <span class="relevance" :title="$t('intelligence.relevance') + ': ' + (item.relevance_score * 100).toFixed(0) + '%'">
              <span class="relevance-bar" :style="{ width: (item.relevance_score * 100) + '%' }"></span>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { intelligenceApi } from '../api/client'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const disasters = ref([])
const selectedDisasterId = ref(null)
const daysBack = ref(90)
const loading = ref(false)
const intel = ref(null)
const categoryFilter = ref('')
const sourceFilter = ref('')

const selectedDisaster = computed(() => {
  if (!selectedDisasterId.value) return null
  return disasters.value.find(d => d.disaster_id === selectedDisasterId.value) || null
})

const availableCategories = computed(() => {
  if (!intel.value) return []
  return Object.keys(intel.value.categories)
})

const filteredItems = computed(() => {
  if (!intel.value) return []
  return intel.value.items.filter(item => {
    if (categoryFilter.value && item.category !== categoryFilter.value) return false
    if (sourceFilter.value && item.source !== sourceFilter.value) return false
    return true
  })
})

const CATEGORY_COLORS = {
  sitrep: '#3498db',
  alert: '#e74c3c',
  news: '#e8913a',
  analysis: '#9b59b6',
  assessment: '#2ecc71',
  report: '#1abc9c',
  map: '#f39c12',
  funding: '#27ae60',
  system: '#95a5a6',
  other: '#7f8c8d',
}

function categoryColor(cat) {
  return CATEGORY_COLORS[cat] || '#7f8c8d'
}

function formatCategory(cat) {
  const labels = {
    sitrep: 'Situation Report',
    alert: 'Alert',
    news: 'News',
    analysis: 'Analysis',
    assessment: 'Assessment',
    report: 'Report',
    map: 'Map / Infographic',
    funding: 'Funding / Appeal',
  }
  return labels[cat] || cat.charAt(0).toUpperCase() + cat.slice(1)
}

function formatDate(dt) {
  if (!dt) return ''
  const d = new Date(dt)
  if (isNaN(d.getTime())) return dt
  const now = new Date()
  const diffMs = now - d
  const diffH = diffMs / (1000 * 60 * 60)
  if (diffH < 1) return `${Math.round(diffMs / 60000)}m ago`
  if (diffH < 24) return `${Math.round(diffH)}h ago`
  if (diffH < 48) return 'Yesterday'
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatTime(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
}

function formatPop(n) {
  if (!n) return '-'
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return Math.round(n / 1000) + 'K'
  return n.toLocaleString()
}

function onDisasterChange() {
  loadIntelligence()
}

async function loadIntelligence() {
  if (!selectedDisasterId.value) return
  loading.value = true
  intel.value = null
  categoryFilter.value = ''
  sourceFilter.value = ''
  try {
    const { data } = await intelligenceApi.get(selectedDisasterId.value, { days_back: daysBack.value, limit: 100 })
    intel.value = data
  } catch (e) {
    handleError(e, 'Failed to load intelligence')
  } finally {
    loading.value = false
  }
}

async function loadDisasters() {
  try {
    const { data } = await intelligenceApi.list()
    disasters.value = data.disasters || []
  } catch (e) {
    handleError(e, 'Failed to load disasters')
  }
}

function retryLoad() {
  clearError()
  loadDisasters()
}

onMounted(loadDisasters)
</script>

<style scoped>
.intelligence {
  display: flex;
  flex-direction: column;
  gap: 20px;
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

.controls-bar {
  display: flex;
  align-items: flex-end;
  gap: 20px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.control-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
}

.control-select {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: 13px;
  min-width: 220px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64px;
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

@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64px 24px;
  text-align: center;
  color: var(--text-secondary);
}

.empty-state svg {
  opacity: 0.3;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 18px;
  color: var(--text);
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 14px;
  max-width: 400px;
}

.empty-state.small {
  padding: 32px;
}

/* Layout */
.intel-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 20px;
  align-items: start;
}

@media (max-width: 900px) {
  .intel-layout {
    grid-template-columns: 1fr;
  }
}

/* Sidebar */
.intel-sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: sticky;
  top: 0;
}

.stats-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}

.stats-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.stat-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 0;
  font-size: 13px;
}

.stat-row.clickable {
  cursor: pointer;
  padding: 5px 4px;
  margin: 0 -4px;
  border-radius: var(--radius-sm);
}

.stat-row.clickable:hover {
  background: var(--bg);
}

.stat-label {
  color: var(--text-secondary);
}

.stat-label.active {
  color: var(--accent);
  font-weight: 600;
}

.stat-value {
  color: var(--text);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.stat-count {
  background: var(--bg);
  color: var(--text);
  font-size: 11px;
  font-weight: 700;
  min-width: 24px;
  height: 20px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  font-variant-numeric: tabular-nums;
}

.cat-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-inline-end: 6px;
  vertical-align: middle;
}

.type-badge {
  text-transform: capitalize;
}

.sev-catastrophic { color: #e74c3c; }
.sev-major { color: #e8913a; }
.sev-moderate { color: #f39c12; }
.sev-minor { color: #3498db; }

/* Feed */
.intel-feed {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.intel-item {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 20px;
  border-inline-start: 3px solid var(--border);
  transition: border-color 0.15s;
}

.intel-item:hover {
  border-inline-start-color: var(--accent);
}

.intel-item.cat-alert {
  border-inline-start-color: #e74c3c;
}

.intel-item.cat-sitrep {
  border-inline-start-color: #3498db;
}

.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 8px;
  flex-wrap: wrap;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.cat-badge {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 2px 8px;
  border-radius: 3px;
  color: #fff;
}

.source-badge {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
}

.alert-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 3px;
  text-transform: uppercase;
}

.alert-red { background: #e74c3c; color: #fff; }
.alert-orange { background: #e8913a; color: #fff; }
.alert-green { background: #27ae60; color: #fff; }

.item-date {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.item-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 6px;
  line-height: 1.4;
}

.item-title a {
  color: var(--text);
  text-decoration: none;
}

.item-title a:hover {
  color: var(--accent);
}

.item-summary {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 10px;
}

.item-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.item-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  font-size: 10px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 3px;
  background: var(--bg);
  color: var(--text-secondary);
}

.type-tag {
  border: 1px solid var(--border);
  text-transform: capitalize;
}

.relevance {
  width: 60px;
  height: 4px;
  background: var(--bg);
  border-radius: 2px;
  overflow: hidden;
  flex-shrink: 0;
}

.relevance-bar {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.3s;
}

@media (max-width: 600px) {
  .controls-bar {
    flex-direction: column;
    align-items: stretch;
  }
  .control-select {
    min-width: auto;
    width: 100%;
  }
}
</style>
