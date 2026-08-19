<template>
  <div class="prepositioning">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="page-header">
      <h2>{{ $t('prepositioning.title') }}</h2>
      <p class="page-subtitle">{{ $t('prepositioning.subtitle') }}</p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>{{ $t('prepositioning.analyzingCoverage') }}</span>
    </div>

    <template v-else>
      <!-- Map showing warehouses + risk zones -->
      <div class="map-section">
        <div class="panel-header">
          <h3 class="panel-title">{{ $t('prepositioning.coverageMap') }}</h3>
          <div class="legend">
            <span class="legend-item"><span class="dot blue"></span> {{ $t('prepositioning.warehouse') }}</span>
            <span class="legend-item"><span class="dot red"></span> {{ $t('prepositioning.highRiskZone') }}</span>
            <span class="legend-item"><span class="dot yellow"></span> {{ $t('prepositioning.moderateRiskZone') }}</span>
          </div>
        </div>
        <div class="map-wrapper">
          <MapView :markers="mapMarkers" :center="[10, 35]" :zoom="3" />
        </div>
      </div>

      <!-- Recommendations -->
      <div class="recommendations">
        <h3 class="section-title">{{ $t('prepositioning.warehouseRecommendations') }}</h3>
        <div
          v-for="rec in recommendations"
          :key="rec.warehouse_id"
          class="rec-card"
          :class="{ expanded: expandedId === rec.warehouse_id }"
          @click="expandedId = expandedId === rec.warehouse_id ? null : rec.warehouse_id"
        >
          <div class="rec-header">
            <div class="rec-rank">#{{ rec.rank }}</div>
            <div class="rec-info">
              <div class="rec-name">{{ rec.warehouse_name }}</div>
              <div class="rec-location">{{ rec.location }}</div>
            </div>
            <div class="rec-scores">
              <div class="score-pill" :class="scoreClass(rec.average_coverage_score)">
                {{ rec.average_coverage_score.toFixed(0) }}
                <span class="score-label">{{ $t('prepositioning.coverage') }}</span>
              </div>
              <div class="zones-count">
                {{ rec.zones_covered }} {{ $t('prepositioning.zones') }}
              </div>
            </div>
            <span class="expand-arrow" :class="{ open: expandedId === rec.warehouse_id }">&#9660;</span>
          </div>

          <div v-if="expandedId === rec.warehouse_id" class="rec-details" @click.stop>
            <!-- Stock suggestions -->
            <div class="detail-section">
              <h4>{{ $t('prepositioning.stockRecommendations') }}</h4>
              <div class="suggestions-grid">
                <div
                  v-for="s in rec.stock_suggestions"
                  :key="s.category"
                  class="suggestion-card"
                  :class="'priority-' + s.priority"
                >
                  <div class="sug-cat">{{ s.category }}</div>
                  <div class="sug-priority">{{ s.priority }}</div>
                  <div class="sug-reason">{{ s.reason }}</div>
                </div>
              </div>
            </div>

            <!-- Current stock -->
            <div v-if="rec.current_stock_by_category?.length" class="detail-section">
              <h4>{{ $t('prepositioning.currentStock') }}</h4>
              <div class="stock-cats">
                <div v-for="cat in rec.current_stock_by_category" :key="cat.category" class="stock-cat">
                  <div class="stock-cat-header">
                    <span class="cat-name">{{ cat.category }}</span>
                    <span class="cat-total">{{ cat.total_quantity.toLocaleString() }} {{ $t('prepositioning.units') }}</span>
                  </div>
                  <div class="stock-items">
                    <div v-for="item in cat.items" :key="item.sku" class="stock-item">
                      <span class="item-name">{{ item.name }}</span>
                      <span class="item-qty">{{ item.quantity.toLocaleString() }} {{ item.unit }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Covered zones -->
            <div class="detail-section">
              <h4>{{ $t('prepositioning.riskZoneCoverage') }}</h4>
              <table class="zones-table">
                <thead><tr><th>{{ $t('prepositioning.zone') }}</th><th>{{ $t('prepositioning.distance') }}</th><th>{{ $t('prepositioning.coverageScore') }}</th></tr></thead>
                <tbody>
                  <tr v-for="z in rec.covered_zones" :key="z.zone_name">
                    <td>{{ z.zone_name }}</td>
                    <td>{{ z.distance_km.toFixed(0) }} {{ $t('prepositioning.km') }}</td>
                    <td>
                      <div class="score-bar-track">
                        <div class="score-bar-fill" :style="{ width: z.coverage_score + '%' }" :class="scoreClass(z.coverage_score)"></div>
                      </div>
                      <span class="score-val">{{ z.coverage_score.toFixed(1) }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Risk Zones table -->
      <div class="risk-section">
        <h3 class="section-title">{{ $t('prepositioning.activeRiskZones') }}</h3>
        <DataTable
          :columns="riskColumns"
          :rows="riskZones"
          :empty-text="$t('prepositioning.noRiskZones')"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { prepositioningApi } from '../api/client'
import MapView from '../components/common/MapView.vue'
import DataTable from '../components/common/DataTable.vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { useErrorHandler } from '../composables/useErrorHandler'

const { t } = useI18n()
const { error, handleError, clearError } = useErrorHandler()

const recommendations = ref([])
const riskZones = ref([])
const loading = ref(true)
const expandedId = ref(null)

const riskColumns = computed(() => [
  { key: 'name', label: t('prepositioning.region') },
  { key: 'risk_level', label: t('prepositioning.riskLevel') },
  { key: 'risk_score', label: t('prepositioning.score'), format: v => v?.toFixed(1) },
  { key: 'dominant_hazard', label: t('prepositioning.primaryHazard') },
])

const mapMarkers = computed(() => {
  const markers = []
  for (const rec of recommendations.value) {
    const [lat, lng] = rec.location.split(',').map(Number)
    if (!isNaN(lat) && !isNaN(lng)) {
      markers.push({
        lat, lng,
        color: 'blue',
        radius: 10,
        popup: `<strong>${rec.warehouse_name}</strong><br/>Coverage: ${rec.average_coverage_score.toFixed(0)}`,
      })
    }
  }
  for (const z of riskZones.value) {
    markers.push({
      lat: z.latitude, lng: z.longitude,
      color: z.risk_level === 'very_high' || z.risk_level === 'high' ? 'red' : 'yellow',
      radius: 12,
      pulse: z.risk_level === 'very_high',
      popup: `<strong>${z.name}</strong><br/>Risk: ${z.risk_score.toFixed(1)} (${z.risk_level})<br/>Primary: ${z.dominant_hazard}`,
    })
  }
  return markers
})

function scoreClass(score) {
  if (score >= 60) return 'high'
  if (score >= 30) return 'medium'
  return 'low'
}

async function fetchData() {
  loading.value = true
  clearError()
  try {
    const { data } = await prepositioningApi.recommendations()
    recommendations.value = data.recommendations || []
    riskZones.value = data.risk_zones || []
  } catch (e) {
    handleError(e, 'Failed to load prepositioning data')
  } finally {
    loading.value = false
  }
}

function retryLoad() {
  clearError()
  fetchData()
}

onMounted(fetchData)
</script>

<style scoped>
.prepositioning { max-width: 1200px; }
.page-header { margin-bottom: 24px; }
.page-header h2 { font-size: 24px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.page-subtitle { font-size: 14px; color: var(--text-secondary); }

.map-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 24px;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; border-bottom: 1px solid var(--border);
}
.panel-title { font-size: 15px; font-weight: 600; color: var(--text); }
.legend { display: flex; gap: 16px; font-size: 12px; color: var(--text-secondary); }
.legend-item { display: flex; align-items: center; gap: 5px; }
.dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot.blue { background: var(--primary); }
.dot.red { background: var(--danger); }
.dot.yellow { background: var(--accent); }
.map-wrapper { height: 350px; }

.section-title { font-size: 17px; font-weight: 600; color: var(--text); margin-bottom: 16px; }

.recommendations { margin-bottom: 32px; }

.rec-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: 10px;
  cursor: pointer;
  transition: border-color 0.15s ease;
}
.rec-card:hover { border-color: var(--primary); }
.rec-card.expanded { border-color: var(--primary); }

.rec-header {
  display: flex; align-items: center; gap: 16px; padding: 16px 20px;
}
.rec-rank {
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--primary); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 14px; flex-shrink: 0;
}
.rec-info { flex: 1; }
.rec-name { font-weight: 600; font-size: 15px; color: var(--text); }
.rec-location { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.rec-scores { display: flex; align-items: center; gap: 12px; }

.score-pill {
  display: flex; flex-direction: column; align-items: center;
  padding: 6px 14px; border-radius: var(--radius); font-weight: 700; font-size: 18px;
  font-variant-numeric: tabular-nums;
}
.score-pill.high { background: rgba(39,174,96,0.12); color: var(--success); }
.score-pill.medium { background: rgba(232,145,58,0.12); color: var(--accent); }
.score-pill.low { background: rgba(231,76,60,0.12); color: var(--danger); }
.score-label { font-size: 10px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }

.zones-count { font-size: 13px; color: var(--text-secondary); white-space: nowrap; }

.expand-arrow {
  font-size: 10px; color: var(--text-secondary);
  transition: transform 0.2s ease;
}
.expand-arrow.open { transform: rotate(180deg); }

.rec-details {
  padding: 0 20px 20px;
  border-top: 1px solid var(--border);
  cursor: default;
}

.detail-section { margin-top: 20px; }
.detail-section h4 {
  font-size: 13px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.5px; color: var(--text-secondary); margin-bottom: 10px;
}

.suggestions-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; }
.suggestion-card {
  padding: 12px; border-radius: var(--radius-sm);
  border: 1px solid var(--border); background: var(--bg);
}
.sug-cat { font-weight: 600; text-transform: capitalize; font-size: 14px; color: var(--text); }
.sug-priority { font-size: 11px; font-weight: 600; text-transform: uppercase; margin: 4px 0; }
.priority-high .sug-priority { color: var(--danger); }
.priority-medium .sug-priority { color: var(--accent); }
.sug-reason { font-size: 12px; color: var(--text-secondary); line-height: 1.4; }

.stock-cats { display: flex; flex-direction: column; gap: 12px; }
.stock-cat-header {
  display: flex; justify-content: space-between; padding: 8px 12px;
  background: var(--bg); border-radius: var(--radius-sm); font-size: 13px; font-weight: 600;
}
.cat-name { text-transform: capitalize; color: var(--text); }
.cat-total { color: var(--text-secondary); }
.stock-items { padding: 4px 12px; }
.stock-item { display: flex; justify-content: space-between; padding: 4px 0; font-size: 13px; border-bottom: 1px solid var(--border); }
.stock-item:last-child { border-bottom: none; }
.item-name { color: var(--text); }
.item-qty { color: var(--text-secondary); font-variant-numeric: tabular-nums; }

.zones-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.zones-table th {
  text-align: left; padding: 8px 12px; font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
}
.zones-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); color: var(--text); }
.score-bar-track {
  display: inline-block; width: 60px; height: 6px;
  background: var(--bg); border-radius: 3px; overflow: hidden; vertical-align: middle; margin-right: 8px;
}
.score-bar-fill { height: 100%; border-radius: 3px; }
.score-bar-fill.high { background: var(--success); }
.score-bar-fill.medium { background: var(--accent); }
.score-bar-fill.low { background: var(--danger); }
.score-val { font-variant-numeric: tabular-nums; }

.risk-section { margin-top: 8px; }

.loading-state, .error-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 64px 24px; color: var(--text-secondary); gap: 12px;
}
.spinner { width: 28px; height: 28px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.retry-btn { padding: 8px 20px; border: 1px solid var(--primary); border-radius: var(--radius-sm); background: transparent; color: var(--primary); font-size: 13px; cursor: pointer; }
</style>
