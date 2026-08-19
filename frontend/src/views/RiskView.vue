<template>
  <div class="risk-dashboard">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="page-header">
      <h2>{{ $t('risk.title') }}</h2>
      <p class="page-subtitle">{{ $t('risk.subtitle') }}</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>{{ $t('risk.loadingData') }}</span>
    </div>

    <template v-else>
      <!-- Map -->
      <div class="map-section">
        <div class="map-wrapper">
          <MapView :markers="mapMarkers" :center="[15, 30]" :zoom="2" />
        </div>
      </div>

      <!-- Legend -->
      <div class="legend">
        <span class="legend-title">{{ $t('risk.riskLevel') }}:</span>
        <span class="legend-item"><span class="legend-dot" style="background: #e74c3c;"></span> {{ $t('risk.critical') }}</span>
        <span class="legend-item"><span class="legend-dot" style="background: #f39c12;"></span> {{ $t('risk.high') }}</span>
        <span class="legend-item"><span class="legend-dot" style="background: #3498db;"></span> {{ $t('risk.moderate') }}</span>
        <span class="legend-item"><span class="legend-dot" style="background: #27ae60;"></span> {{ $t('risk.low') }}</span>
      </div>

      <!-- Region Cards -->
      <div class="regions-section">
        <h3 class="section-title">{{ $t('risk.riskRegions') }} ({{ sortedRegions.length }})</h3>
        <div class="regions-list">
          <div v-for="region in sortedRegions" :key="region.name" class="region-card">
            <div class="region-header" @click="toggleRegion(region.name)">
              <div class="region-info">
                <h4 class="region-name">{{ region.name }}</h4>
                <div class="region-meta">
                  <span class="composite-score">{{ $t('risk.score') }}: {{ region.composite_risk_score?.toFixed(3) }}</span>
                  <StatusBadge :status="region.risk_level" size="sm" />
                </div>
              </div>
              <span class="expand-icon" :class="{ expanded: expandedRegions.has(region.name) }">&#9662;</span>
            </div>

            <div v-if="expandedRegions.has(region.name)" class="region-details">
              <!-- Hazard Breakdown -->
              <div class="detail-section">
                <h5 class="detail-title">{{ $t('risk.hazardBreakdown') }}</h5>
                <div class="bar-chart">
                  <div v-for="(score, hazard) in region.hazards" :key="hazard" class="bar-container">
                    <div class="bar-label">{{ formatHazard(hazard) }}</div>
                    <div class="bar-track">
                      <div
                        class="bar-fill"
                        :style="{ width: score + '%', background: hazardBarColor(score) }"
                      ></div>
                    </div>
                    <div class="bar-value">{{ Math.round(score) }}%</div>
                  </div>
                </div>
              </div>

              <!-- Stats -->
              <div class="detail-stats">
                <div class="stat-item">
                  <span class="stat-label">{{ $t('risk.populationExposure') }}</span>
                  <span class="stat-value">{{ region.population_exposure?.toLocaleString() }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">{{ $t('risk.infrastructureVulnerability') }}</span>
                  <span class="stat-value">{{ Math.round(region.infrastructure_vulnerability || 0) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { riskApi } from '../api/client'
import MapView from '../components/common/MapView.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const regions = ref([])
const loading = ref(true)
const expandedRegions = ref(new Set())

const riskColors = {
  critical: '#e74c3c',
  high: '#f39c12',
  moderate: '#3498db',
  low: '#27ae60'
}

const sortedRegions = computed(() => {
  return [...regions.value].sort((a, b) => (b.composite_risk_score || 0) - (a.composite_risk_score || 0))
})

const mapMarkers = computed(() => {
  return regions.value
    .filter(r => r.lat != null && r.lng != null)
    .map(r => {
      const pop = r.population_exposure || 0
      const radius = (pop / 5000000) * 8 + 5
      return {
        lat: r.lat,
        lng: r.lng,
        radius: Math.max(5, Math.min(radius, 30)),
        color: riskColors[r.risk_level] || '#3498db',
        popup: `<strong>${r.name}</strong><br/>Risk: ${r.risk_level}<br/>Score: ${r.composite_risk_score?.toFixed(3)}<br/>Pop: ${r.population_exposure?.toLocaleString()}`
      }
    })
})

function toggleRegion(name) {
  if (expandedRegions.value.has(name)) {
    expandedRegions.value.delete(name)
  } else {
    expandedRegions.value.add(name)
  }
  // Force reactivity on Set
  expandedRegions.value = new Set(expandedRegions.value)
}

function formatHazard(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function hazardBarColor(score) {
  if (score >= 70) return 'var(--danger)'
  if (score >= 40) return 'var(--warning)'
  return 'var(--success)'
}

async function fetchRiskData() {
  loading.value = true
  clearError()
  try {
    const { data } = await riskApi.map()
    const raw = Array.isArray(data) ? data : data.regions || []
    regions.value = raw.map(r => ({
      ...r,
      name: r.region_name || r.name || r.region,
      lat: r.latitude ?? r.lat,
      lng: r.longitude ?? r.lng,
      composite_risk_score: r.composite_score ?? r.composite_risk_score,
      hazards: r.hazard_breakdown || r.hazards || {},
      population_exposure: r.components?.population_exposure ?? r.population_exposure ?? 0,
      infrastructure_vulnerability: r.components?.infrastructure_vulnerability ?? r.infrastructure_vulnerability ?? 0,
    }))
  } catch (e) {
    handleError(e, 'Failed to load risk data')
  } finally {
    loading.value = false
  }
}

function retryLoad() {
  clearError()
  fetchRiskData()
}

onMounted(fetchRiskData)
</script>

<style scoped>
.risk-dashboard {
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

.map-section {
  margin-bottom: 12px;
}

.map-wrapper {
  height: 420px;
  border-radius: var(--radius);
  overflow: hidden;
}

.legend {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: 24px;
  font-size: 13px;
  flex-wrap: wrap;
}

.legend-title {
  font-weight: 600;
  color: var(--text);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.regions-section {
  margin-top: 8px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 12px;
}

.regions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.region-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.15s ease;
}

.region-card:hover {
  border-color: var(--primary);
}

.region-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  cursor: pointer;
  user-select: none;
}

.region-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.region-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.region-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.composite-score {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.expand-icon {
  font-size: 14px;
  color: var(--text-secondary);
  transition: transform 0.2s ease;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.region-details {
  border-top: 1px solid var(--border);
  padding: 20px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
  margin-bottom: 12px;
}

/* Bar chart */
.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bar-container {
  display: grid;
  grid-template-columns: 100px 1fr 50px;
  align-items: center;
  gap: 12px;
}

.bar-label {
  font-size: 13px;
  color: var(--text);
  font-weight: 500;
  text-align: right;
}

.bar-track {
  height: 20px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: var(--radius-sm);
  transition: width 0.6s ease;
}

.bar-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.detail-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-item {
  background: var(--bg);
  border-radius: var(--radius-sm);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
}

.loading-state,
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

@media (max-width: 768px) {
  .detail-stats {
    grid-template-columns: 1fr;
  }

  .bar-container {
    grid-template-columns: 80px 1fr 40px;
  }
}
</style>
