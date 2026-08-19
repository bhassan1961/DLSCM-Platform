<template>
  <div class="compliance-view">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="page-header">
      <div>
        <h2>{{ $t('compliance.title') }}</h2>
        <p class="subtitle">{{ $t('compliance.subtitle') }}</p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>{{ $t('compliance.loadingData') }}</span>
    </div>

    <template v-else>
      <!-- Overall Score -->
      <div class="score-card" :class="scoreColor">
        <div class="score-value">{{ complianceData.overall_score ?? '--' }}</div>
        <div class="score-label">{{ $t('compliance.overallScore') }}</div>
      </div>

      <!-- Sphere Standards -->
      <section class="section">
        <h3 class="section-title">{{ $t('compliance.sphereStandards') }}</h3>
        <div class="cards-grid">
          <div v-for="std in sphereStandards" :key="std.name" class="standard-card">
            <div class="standard-header">
              <h4>{{ std.standard }}</h4>
              <span class="status-indicator" :class="statusClass(std.status)">
                {{ formatStatus(std.status) }}
              </span>
            </div>
            <p class="standard-desc" v-if="std.description">{{ std.description }}</p>
            <div class="standard-values">
              <div class="value-pair">
                <span class="value-label">{{ $t('common.current') }}</span>
                <span class="value-num">{{ std.current_value ?? '-' }}</span>
              </div>
              <div class="value-pair">
                <span class="value-label">{{ $t('common.target') }}</span>
                <span class="value-num">{{ std.target_value ?? '-' }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Inventory Health -->
      <section class="section">
        <h3 class="section-title">{{ $t('compliance.inventoryHealth') }}</h3>
        <div class="cards-grid cols-4">
          <div class="metric-card">
            <div class="metric-value">{{ inventoryHealth.total_items ?? 0 }}</div>
            <div class="metric-label">{{ $t('compliance.totalItems') }}</div>
          </div>
          <div class="metric-card warning-card">
            <div class="metric-value">{{ inventoryHealth.items_expiring_30_days ?? 0 }}</div>
            <div class="metric-label">{{ $t('compliance.expiring30Days') }}</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{{ inventoryHealth.items_expiring_90_days ?? 0 }}</div>
            <div class="metric-label">{{ $t('compliance.expiring90Days') }}</div>
          </div>
          <div class="metric-card danger-card">
            <div class="metric-value">{{ inventoryHealth.stockout_risk_count ?? 0 }}</div>
            <div class="metric-label">{{ $t('compliance.stockoutRisk') }}</div>
          </div>
        </div>
      </section>

      <!-- Operational Metrics -->
      <section class="section">
        <h3 class="section-title">{{ $t('compliance.operationalMetrics') }}</h3>
        <div class="cards-grid cols-3">
          <div class="metric-card">
            <div class="metric-value">{{ operationalMetrics.avg_request_fulfillment_days ?? '-' }}</div>
            <div class="metric-label">{{ $t('compliance.avgFulfillment') }}</div>
          </div>
          <div class="metric-card" :class="{ 'warning-card': (operationalMetrics.requests_overdue ?? 0) > 0 }">
            <div class="metric-value">{{ operationalMetrics.requests_overdue ?? 0 }}</div>
            <div class="metric-label">{{ $t('compliance.overdueRequests') }}</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{{ operationalMetrics.delivery_success_rate ?? '-' }}%</div>
            <div class="metric-label">{{ $t('compliance.deliverySuccessRate') }}</div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { complianceApi } from '../api/client'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const loading = ref(true)
const complianceData = ref({})

const sphereStandards = computed(() => complianceData.value.sphere_standards || [])
const inventoryHealth = computed(() => complianceData.value.inventory_health || {})
const operationalMetrics = computed(() => complianceData.value.operational_metrics || {})

const scoreColor = computed(() => {
  const score = complianceData.value.overall_score
  if (score == null) return ''
  if (score > 70) return 'score-green'
  if (score >= 40) return 'score-yellow'
  return 'score-red'
})

function statusClass(status) {
  const map = { met: 'status-met', at_risk: 'status-risk', not_met: 'status-not-met' }
  return map[status] || 'status-risk'
}

function formatStatus(status) {
  if (!status) return 'Unknown'
  return status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

async function loadComplianceData() {
  loading.value = true
  clearError()
  try {
    const { data } = await complianceApi.check()
    complianceData.value = data || {}
  } catch (e) {
    handleError(e, 'Failed to load compliance data')
  } finally {
    loading.value = false
  }
}

function retryLoad() {
  clearError()
  loadComplianceData()
}

onMounted(loadComplianceData)
</script>

<style scoped>
.compliance-view {
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

/* Score Card */
.score-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 32px;
  text-align: center;
}

.score-value {
  font-size: 56px;
  font-weight: 700;
  line-height: 1.1;
}

.score-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 8px;
}

.score-green .score-value { color: var(--success); }
.score-yellow .score-value { color: var(--warning); }
.score-red .score-value { color: var(--danger); }

/* Sections */
.section { display: flex; flex-direction: column; gap: 12px; }

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.cards-grid.cols-4 {
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}

.cards-grid.cols-3 {
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
}

/* Standard Cards */
.standard-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}

.standard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.standard-header h4 {
  font-size: 15px;
  color: var(--text);
  margin: 0;
  text-transform: capitalize;
}

.status-indicator {
  padding: 2px 10px;
  border-radius: var(--radius);
  font-size: 11px;
  font-weight: 600;
}

.status-met {
  background: rgba(39, 174, 96, 0.12);
  color: var(--success);
}

.status-risk {
  background: rgba(243, 156, 18, 0.12);
  color: var(--warning);
}

.status-not-met {
  background: rgba(231, 76, 60, 0.12);
  color: var(--danger);
}

.standard-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 12px;
}

.standard-values {
  display: flex;
  gap: 24px;
}

.value-pair { display: flex; flex-direction: column; }

.value-label {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.value-num {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
}

/* Metric Cards */
.metric-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  text-align: center;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
}

.metric-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.warning-card {
  border-color: var(--warning);
}

.warning-card .metric-value {
  color: var(--warning);
}

.danger-card {
  border-color: var(--danger);
}

.danger-card .metric-value {
  color: var(--danger);
}
</style>
