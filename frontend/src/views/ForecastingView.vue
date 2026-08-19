<template>
  <div class="forecasting">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <!-- Controls -->
    <div class="controls-bar">
      <div class="control-group">
        <label class="control-label">{{ $t('forecasting.disaster') }}</label>
        <select v-model="selectedDisaster" class="control-select" @change="onDisasterChange">
          <option :value="null" disabled>{{ $t('forecasting.selectDisaster') }}</option>
          <option v-for="d in disasters" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
      </div>
      <div class="control-group">
        <label class="control-label">{{ $t('forecasting.horizon') }}</label>
        <div class="horizon-buttons">
          <button
            v-for="h in horizons"
            :key="h"
            class="horizon-btn"
            :class="{ active: selectedHorizon === h }"
            @click="selectedHorizon = h; fetchForecast()"
          >
            {{ h }} {{ $t('forecasting.days') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>{{ $t('forecasting.generating') }}</span>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && !error && !forecast" class="empty-state">
      <svg class="empty-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>
      <h2 class="empty-title">{{ $t('forecasting.emptyTitle') }}</h2>
      <p>{{ $t('forecasting.emptyDesc') }}</p>
    </div>

    <!-- Results -->
    <template v-if="forecast && !loading">
      <!-- Summary Cards -->
      <div class="summary-cards">
        <div
          v-for="cat in categories"
          :key="cat.key"
          class="summary-card"
          :style="{ borderTopColor: categoryColors[cat.key] }"
        >
          <SvgIcon :name="categoryIconNames[cat.key] || 'package'" :size="22" class="card-icon" :style="{ color: categoryColors[cat.key] }" />
          <div class="card-value">{{ formatNumber(cat.total) }}</div>
          <div class="card-unit">{{ cat.unit }}</div>
          <div class="card-label">{{ formatCategory(cat.key) }}</div>
        </div>
      </div>

      <!-- Chart -->
      <div class="chart-panel">
        <div class="panel-header">
          <h2 class="panel-title">{{ $t('forecasting.dailyForecast') }} &mdash; {{ forecast.disaster_name }}</h2>
          <span class="chart-period">{{ selectedHorizon }} {{ $t('forecasting.dayProjection') }}</span>
        </div>
        <div class="chart-wrapper">
          <Line :data="chartData" :options="chartOptions" />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { disastersApi, forecastApi } from '../api/client'
import SvgIcon from '../components/common/SvgIcon.vue'
import { useErrorHandler } from '../composables/useErrorHandler'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const { error, handleError, clearError } = useErrorHandler()

const disasters = ref([])
const selectedDisaster = ref(null)
const selectedHorizon = ref(30)
const horizons = [7, 14, 30]
const loading = ref(false)
const forecast = ref(null)

const categoryColors = {
  food: '#27ae60',
  water: '#3498db',
  medical: '#e74c3c',
  shelter: '#8e44ad',
  hygiene: '#f39c12',
  nfi: '#1abc9c'
}

const categoryIconNames = {
  food: 'food',
  water: 'water',
  medical: 'medical',
  shelter: 'shelter',
  hygiene: 'hygiene',
  nfi: 'package'
}

const categories = computed(() => {
  if (!forecast.value?.forecasts) return []
  return Object.entries(forecast.value.forecasts).map(([key, data]) => ({
    key,
    total: data.total,
    unit: data.unit,
    daily: data.daily
  }))
})

const chartData = computed(() => {
  if (!forecast.value?.forecasts) return { labels: [], datasets: [] }
  const days = selectedHorizon.value
  const labels = Array.from({ length: days }, (_, i) => `Day ${i + 1}`)
  const datasets = Object.entries(forecast.value.forecasts).map(([key, data]) => ({
    label: formatCategory(key),
    data: data.daily || [],
    borderColor: categoryColors[key] || '#888',
    backgroundColor: hexToRgba(categoryColors[key] || '#888', 0.08),
    fill: true,
    tension: 0.3,
    pointRadius: days <= 14 ? 4 : 2,
    pointHoverRadius: 6,
    borderWidth: 2
  }))
  return { labels, datasets }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false
  },
  plugins: {
    legend: {
      position: 'top',
      labels: {
        usePointStyle: true,
        padding: 16,
        color: '#a0aec0'
      }
    },
    tooltip: {
      backgroundColor: '#1a2332',
      titleColor: '#e2e8f0',
      bodyColor: '#a0aec0',
      borderColor: '#2d3748',
      borderWidth: 1,
      padding: 12,
      cornerRadius: 8
    }
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.06)' },
      ticks: { color: '#718096' }
    },
    y: {
      grid: { color: 'rgba(255,255,255,0.06)' },
      ticks: { color: '#718096' },
      beginAtZero: true
    }
  }
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r},${g},${b},${alpha})`
}

function formatCategory(cat) {
  if (!cat) return '-'
  if (cat === 'nfi') return 'NFI'
  return cat.charAt(0).toUpperCase() + cat.slice(1)
}

function formatNumber(n) {
  if (n == null) return '-'
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return n.toLocaleString()
}

function onDisasterChange() {
  forecast.value = null
  clearError()
  if (selectedDisaster.value) {
    fetchForecast()
  }
}

async function fetchForecast() {
  if (!selectedDisaster.value) return
  loading.value = true
  clearError()
  try {
    const { data } = await forecastApi.forecast(selectedDisaster.value, selectedHorizon.value)
    forecast.value = data
  } catch (e) {
    handleError(e, 'Failed to generate forecast. Please try again.')
    forecast.value = null
  } finally {
    loading.value = false
  }
}

async function loadDisasters() {
  try {
    const { data } = await disastersApi.list()
    disasters.value = data?.disasters || data || []
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
.forecasting {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.controls-bar {
  display: flex;
  align-items: flex-end;
  gap: 24px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.control-label {
  font-size: 11px;
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

.horizon-buttons {
  display: flex;
  gap: 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.horizon-btn {
  padding: 8px 16px;
  border: none;
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  border-right: 1px solid var(--border);
}

.horizon-btn:last-child {
  border-right: none;
}

.horizon-btn:hover {
  background: var(--bg);
  color: var(--text);
}

.horizon-btn.active {
  background: var(--primary);
  color: #ffffff;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 16px;
}

@media (max-width: 1200px) {
  .summary-cards {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .summary-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

.summary-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-top: 3px solid var(--primary);
  border-radius: var(--radius);
  padding: 16px;
  text-align: center;
}

.card-icon {
  margin-bottom: 8px;
}

.card-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
}

.card-unit {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.card-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-top: 6px;
  text-transform: capitalize;
}

.chart-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
  gap: 8px;
}

.panel-header .panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.chart-period {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg);
  padding: 4px 10px;
  border-radius: var(--radius);
}

.chart-wrapper {
  padding: 20px;
  height: 360px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px;
  color: var(--text-secondary);
  font-size: 14px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.empty-icon {
  opacity: 0.4;
  margin-bottom: 16px;
}

.empty-state .empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 14px;
  color: var(--text-secondary);
}

.error-banner {
  background: rgba(231, 76, 60, 0.1);
  border: 1px solid var(--danger);
  border-radius: var(--radius);
  padding: 12px 20px;
  color: var(--danger);
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
</style>
