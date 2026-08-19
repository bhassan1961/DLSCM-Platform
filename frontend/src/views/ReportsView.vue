<template>
  <div class="reports">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <!-- Tab Header -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        <SvgIcon :name="tab.iconName" :size="16" class="tab-icon" />
        {{ $t('reports.tab_' + tab.key) }}
      </button>
    </div>

    <!-- Donor Reports Tab -->
    <div v-if="activeTab === 'donor'" class="tab-content">
      <div class="controls-panel">
        <div class="panel-header">
          <h3>{{ $t('reports.generateDonorReport') }}</h3>
        </div>
        <div class="controls-body">
          <div class="control-row">
            <div class="control-group">
              <label class="control-label" for="donor-disaster">{{ $t('reports.disaster') }}</label>
              <select id="donor-disaster" v-model="donorDisaster" class="control-select">
                <option :value="null" disabled>{{ $t('reports.selectDisaster') }}</option>
                <option v-for="d in disasters" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </div>
            <div class="control-group">
              <label class="control-label" for="period-start">{{ $t('reports.periodStart') }}</label>
              <input id="period-start" type="date" v-model="periodStart" class="control-input" />
            </div>
            <div class="control-group">
              <label class="control-label" for="period-end">{{ $t('reports.periodEnd') }}</label>
              <input id="period-end" type="date" v-model="periodEnd" class="control-input" />
            </div>
            <div class="control-group">
              <label class="control-label" for="report-template">{{ $t('reports.template') }}</label>
              <select id="report-template" v-model="selectedTemplate" class="control-select">
                <option value="generic">{{ $t('reports.templateGeneric') }}</option>
                <option value="echo">{{ $t('reports.templateEcho') }}</option>
                <option value="usaid">{{ $t('reports.templateUsaid') }}</option>
                <option value="fcdo">{{ $t('reports.templateFcdo') }}</option>
              </select>
            </div>
            <div class="control-group action-group">
              <button
                class="generate-btn"
                :disabled="!donorDisaster || !periodStart || !periodEnd || donorLoading"
                @click="generateReport"
              >
                <span v-if="donorLoading" class="btn-spinner"></span>
                {{ donorLoading ? 'Generating...' : 'Generate Report' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Donor Error -->
      <div v-if="donorError" class="error-banner" role="alert">
        {{ donorError }}
      </div>

      <!-- Donor Report Output -->
      <div v-if="donorReport" class="report-output">
        <div class="report-header">
          <div class="report-title-row">
            <h2>{{ donorReport.title || 'Donor Report' }}</h2>
            <span v-if="donorReport.template && donorReport.template !== 'Generic'" class="template-badge">{{ donorReport.template }}</span>
          </div>
          <span class="report-meta">
            {{ donorReport.period_start }} to {{ donorReport.period_end }}
          </span>
        </div>

        <!-- Executive Summary -->
        <div class="report-section" v-if="donorReport.executive_summary || donorReport.summary">
          <h3>Executive Summary</h3>
          <p>{{ donorReport.executive_summary || donorReport.summary }}</p>
        </div>

        <!-- Key Metrics -->
        <div class="report-section" v-if="donorReport.metrics || donorReport.key_metrics">
          <h3>Key Metrics</h3>
          <div class="metrics-grid">
            <div
              v-for="(value, key) in (donorReport.metrics || donorReport.key_metrics)"
              :key="key"
              class="metric-card"
            >
              <div class="metric-value">{{ formatMetric(value) }}</div>
              <div class="metric-label">{{ formatKey(key) }}</div>
            </div>
          </div>
        </div>

        <!-- Expenditure / Financials -->
        <div class="report-section" v-if="donorReport.expenditure || donorReport.financials">
          <h3>Expenditure Breakdown</h3>
          <div class="breakdown-list">
            <div
              v-for="(amount, category) in (donorReport.expenditure || donorReport.financials)"
              :key="category"
              class="breakdown-item"
            >
              <span class="breakdown-label">{{ formatKey(category) }}</span>
              <span class="breakdown-value">{{ formatMoney(amount) }}</span>
            </div>
          </div>
        </div>

        <!-- Beneficiaries -->
        <div class="report-section" v-if="donorReport.beneficiaries">
          <h3>Beneficiary Reach</h3>
          <p v-if="typeof donorReport.beneficiaries === 'string'">{{ donorReport.beneficiaries }}</p>
          <div v-else-if="typeof donorReport.beneficiaries === 'object'" class="breakdown-list">
            <div
              v-for="(count, group) in donorReport.beneficiaries"
              :key="group"
              class="breakdown-item"
            >
              <span class="breakdown-label">{{ formatKey(group) }}</span>
              <span class="breakdown-value">{{ typeof count === 'number' ? count.toLocaleString() : count }}</span>
            </div>
          </div>
        </div>

        <!-- Recommendations -->
        <div class="report-section" v-if="donorReport.recommendations?.length">
          <h3>Recommendations</h3>
          <ul class="recommendations-list">
            <li v-for="(rec, idx) in donorReport.recommendations" :key="idx">{{ rec }}</li>
          </ul>
        </div>

        <!-- Template-specific sections -->
        <div v-if="donorReport.sections" class="template-sections">
          <div class="template-sections-header">
            <h3>{{ donorReport.template }} Report Sections</h3>
          </div>
          <div
            v-for="(val, key) in donorReport.sections"
            :key="key"
            class="template-section-card"
          >
            <div class="template-section-title">{{ formatKey(key) }}</div>
            <div class="template-section-body">
              <p v-if="typeof val === 'string'">{{ val }}</p>
              <div v-else-if="typeof val === 'object' && val !== null" class="indicator-list">
                <div
                  v-for="(v, k) in val"
                  :key="k"
                  class="indicator-item"
                >
                  <span class="indicator-label">{{ formatKey(k) }}</span>
                  <span class="indicator-value">{{ typeof v === 'number' ? v.toLocaleString() : v }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Raw fallback for unknown structures -->
        <div class="report-section" v-for="(val, key) in remainingFields" :key="key">
          <h3>{{ formatKey(key) }}</h3>
          <p v-if="typeof val === 'string'">{{ val }}</p>
          <pre v-else class="raw-json">{{ JSON.stringify(val, null, 2) }}</pre>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="!donorReport && !donorLoading && !donorError" class="empty-state">
        <svg class="empty-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><line x1="8" y1="10" x2="8" y2="16" /><line x1="12" y1="8" x2="12" y2="16" /><line x1="16" y1="12" x2="16" y2="16" /></svg>
        <h3>Generate a donor report</h3>
        <p>Select a disaster and date range to produce a comprehensive report.</p>
      </div>
    </div>

    <!-- Sitrep Parser Tab -->
    <div v-if="activeTab === 'sitrep'" class="tab-content">
      <div class="controls-panel">
        <div class="panel-header">
          <h3>Situation Report Parser</h3>
        </div>
        <div class="controls-body">
          <div class="control-group">
            <label class="control-label" for="sitrep-text">Paste Situation Report Text</label>
            <textarea
              id="sitrep-text"
              v-model="sitrepText"
              class="sitrep-textarea"
              rows="8"
              placeholder="Paste the full text of a situation report here. The AI will extract structured data including disaster type, urgency, affected population, and identified needs..."
            ></textarea>
          </div>
          <button
            class="generate-btn"
            :disabled="!sitrepText.trim() || sitrepLoading"
            @click="parseSitrep"
          >
            <span v-if="sitrepLoading" class="btn-spinner"></span>
            {{ sitrepLoading ? 'Parsing...' : 'Parse Sitrep' }}
          </button>
        </div>
      </div>

      <!-- Sitrep Error -->
      <div v-if="sitrepError" class="error-banner" role="alert">
        {{ sitrepError }}
      </div>

      <!-- Sitrep Results -->
      <div v-if="sitrepResult" class="sitrep-output">
        <div class="sitrep-grid">
          <!-- Disaster Type -->
          <div class="sitrep-card">
            <div class="card-header">
              <span class="card-title">Disaster Type</span>
            </div>
            <div class="card-body">
              <span class="type-badge">{{ sitrepResult.disaster_type || 'Unknown' }}</span>
            </div>
          </div>

          <!-- Urgency -->
          <div class="sitrep-card">
            <div class="card-header">
              <span class="card-title">Urgency Level</span>
            </div>
            <div class="card-body">
              <span
                class="urgency-badge"
                :class="sitrepResult.urgency"
              >
                {{ sitrepResult.urgency || 'Unknown' }}
              </span>
            </div>
          </div>

          <!-- Affected Population -->
          <div class="sitrep-card">
            <div class="card-header">
              <span class="card-title">Affected Population</span>
            </div>
            <div class="card-body">
              <span class="pop-value">
                {{ sitrepResult.affected_population != null ? sitrepResult.affected_population.toLocaleString() : 'Unknown' }}
              </span>
            </div>
          </div>

          <!-- Identified Needs -->
          <div class="sitrep-card wide">
            <div class="card-header">
              <span class="card-title">Identified Needs</span>
            </div>
            <div class="card-body">
              <div class="needs-tags">
                <span
                  v-for="need in (sitrepResult.identified_needs || [])"
                  :key="need"
                  class="need-tag"
                >
                  {{ need }}
                </span>
                <span v-if="!sitrepResult.identified_needs?.length" class="no-data">None identified</span>
              </div>
            </div>
          </div>

          <!-- Summary -->
          <div class="sitrep-card wide">
            <div class="card-header">
              <span class="card-title">Summary</span>
            </div>
            <div class="card-body">
              <p class="summary-text">{{ sitrepResult.summary || 'No summary generated.' }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="!sitrepResult && !sitrepLoading && !sitrepError" class="empty-state">
        <svg class="empty-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg>
        <h3>Parse a situation report</h3>
        <p>Paste a sitrep text to extract structured data using AI.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { disastersApi, reportsApi, sitrepApi } from '../api/client'
import SvgIcon from '../components/common/SvgIcon.vue'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const tabs = [
  { key: 'donor', label: 'Donor Reports', iconName: 'reports' },
  { key: 'sitrep', label: 'Sitrep Parser', iconName: 'audit' }
]

const activeTab = ref('donor')

// -- Shared --
const disasters = ref([])

// -- Donor Reports --
const donorDisaster = ref(null)
const periodStart = ref('')
const periodEnd = ref('')
const selectedTemplate = ref('generic')
const donorLoading = ref(false)
const donorError = ref(null)
const donorReport = ref(null)

// -- Sitrep Parser --
const sitrepText = ref('')
const sitrepLoading = ref(false)
const sitrepError = ref(null)
const sitrepResult = ref(null)

const knownDonorFields = new Set([
  'title', 'period_start', 'period_end',
  'executive_summary', 'summary',
  'metrics', 'key_metrics',
  'expenditure', 'financials',
  'beneficiaries',
  'recommendations',
  'template', 'sections'
])

const remainingFields = computed(() => {
  if (!donorReport.value) return {}
  const result = {}
  for (const [key, val] of Object.entries(donorReport.value)) {
    if (!knownDonorFields.has(key) && val != null && val !== '') {
      result[key] = val
    }
  }
  return result
})

function formatKey(key) {
  if (!key) return ''
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function formatMetric(value) {
  if (typeof value === 'number') return value.toLocaleString()
  return String(value)
}

function formatMoney(amount) {
  if (typeof amount === 'number') {
    return '$' + amount.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })
  }
  return String(amount)
}

async function generateReport() {
  if (!donorDisaster.value || !periodStart.value || !periodEnd.value) return
  donorLoading.value = true
  donorError.value = null
  donorReport.value = null
  try {
    const start = new Date(periodStart.value)
    const end = new Date(periodEnd.value)
    const diffDays = Math.max(1, Math.round((end - start) / (1000 * 60 * 60 * 24)))
    const { data } = await reportsApi.generate({
      disaster_id: donorDisaster.value,
      period_days: diffDays,
      template: selectedTemplate.value
    })
    const c = data.content || {}
    const rs = c.response_summary || {}
    donorReport.value = {
      title: data.title,
      period_start: periodStart.value,
      period_end: periodEnd.value,
      template: c.template || 'Generic',
      sections: c.sections || null,
      executive_summary: `Response report for the ${c.disaster_name || 'Unknown'} disaster (${c.disaster_type || ''}, ${c.severity || ''} severity). Affected population: ${(c.affected_population || 0).toLocaleString()}. During this period, ${rs.total_supply_requests || 0} supply requests were processed with ${rs.fulfilled_requests || 0} fulfilled, ${rs.active_shipments || 0} shipments in transit, and ${rs.total_beneficiaries_reached || 0} beneficiaries reached across ${rs.coordination_activities || 0} coordination activities.`,
      key_metrics: {
        total_requests: rs.total_supply_requests || 0,
        fulfilled: rs.fulfilled_requests || 0,
        active_shipments: rs.active_shipments || 0,
        beneficiaries_reached: rs.total_beneficiaries_reached || 0,
        coordination_activities: rs.coordination_activities || 0,
      },
      recommendations: [
        'Continue monitoring supply pipeline for potential stockouts',
        'Increase coordination with local partners for last-mile delivery',
        'Review prepositioning strategy based on current consumption rates',
      ],
    }
  } catch (e) {
    donorError.value = 'Failed to generate report. Please try again.'
    handleError(e, 'Failed to generate report')
  } finally {
    donorLoading.value = false
  }
}

async function parseSitrep() {
  if (!sitrepText.value.trim()) return
  sitrepLoading.value = true
  sitrepError.value = null
  sitrepResult.value = null
  try {
    const { data } = await sitrepApi.parse(sitrepText.value)
    sitrepResult.value = data
  } catch (e) {
    sitrepError.value = 'Failed to parse situation report. Please try again.'
    handleError(e, 'Failed to parse situation report')
  } finally {
    sitrepLoading.value = false
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
.reports {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.tab-bar {
  display: flex;
  gap: 0;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  background: var(--surface);
  width: fit-content;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  border-right: 1px solid var(--border);
}

.tab-btn:last-child {
  border-right: none;
}

.tab-btn:hover {
  background: var(--bg);
  color: var(--text);
}

.tab-btn.active {
  background: var(--primary);
  color: #ffffff;
}

.tab-icon {
  flex-shrink: 0;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.controls-panel {
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
}

.panel-header h3,
.panel-header .panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.controls-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-row {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-width: 160px;
}

.action-group {
  flex: 0 0 auto;
}

.control-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
}

.control-select,
.control-input {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: 13px;
  width: 100%;
}

.control-input[type="date"] {
  color-scheme: dark;
}

.sitrep-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
  font-family: inherit;
  line-height: 1.6;
  resize: vertical;
}

.sitrep-textarea::placeholder {
  color: var(--text-secondary);
  opacity: 0.7;
}

.generate-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.generate-btn:hover:not(:disabled) {
  filter: brightness(1.1);
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ── Donor Report Output ── */

.report-output {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.report-header {
  padding: 24px 24px 16px;
  border-bottom: 1px solid var(--border);
}

.report-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 6px;
}

.report-meta {
  font-size: 13px;
  color: var(--text-secondary);
}

.report-section {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border);
}

.report-section:last-child {
  border-bottom: none;
}

.report-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.report-section p {
  font-size: 14px;
  color: var(--text);
  line-height: 1.7;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.metric-card {
  background: var(--bg);
  border-radius: var(--radius-sm);
  padding: 14px;
  text-align: center;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
}

.metric-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.breakdown-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.breakdown-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--bg);
  border-radius: var(--radius-sm);
}

.breakdown-label {
  font-size: 14px;
  color: var(--text);
}

.breakdown-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.recommendations-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.recommendations-list li {
  padding: 10px 14px;
  padding-left: 28px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text);
  line-height: 1.5;
  position: relative;
}

.recommendations-list li::before {
  content: '\2022';
  position: absolute;
  left: 14px;
  color: var(--accent);
  font-weight: 700;
}

.report-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.template-badge {
  display: inline-block;
  padding: 3px 12px;
  background: var(--primary);
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
  border-radius: var(--radius);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.template-sections {
  border-top: 1px solid var(--border);
}

.template-sections-header {
  padding: 20px 24px 12px;
}

.template-sections-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.template-section-card {
  margin: 0 24px 16px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.template-section-title {
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  border-bottom: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.03);
}

.template-section-body {
  padding: 14px 16px;
}

.template-section-body p {
  font-size: 14px;
  color: var(--text);
  line-height: 1.7;
  margin: 0;
}

.indicator-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.indicator-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--surface);
  border-radius: var(--radius-sm);
}

.indicator-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.indicator-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.raw-json {
  background: var(--bg);
  border-radius: var(--radius-sm);
  padding: 14px;
  font-size: 12px;
  color: var(--text-secondary);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Courier New', monospace;
}

/* ── Sitrep Output ── */

.sitrep-output {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sitrep-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 900px) {
  .sitrep-grid {
    grid-template-columns: 1fr;
  }
}

.sitrep-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.sitrep-card.wide {
  grid-column: 1 / -1;
}

.card-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
}

.card-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
}

.card-body {
  padding: 16px;
}

.type-badge {
  display: inline-block;
  padding: 6px 16px;
  background: var(--primary);
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  border-radius: var(--radius-lg);
  text-transform: capitalize;
}

.urgency-badge {
  display: inline-block;
  padding: 6px 16px;
  font-size: 14px;
  font-weight: 600;
  border-radius: var(--radius-lg);
  text-transform: capitalize;
}

.urgency-badge.critical {
  background: rgba(231, 76, 60, 0.15);
  color: #e74c3c;
}

.urgency-badge.high {
  background: rgba(232, 145, 58, 0.15);
  color: #e8913a;
}

.urgency-badge.medium {
  background: rgba(243, 156, 18, 0.15);
  color: #f39c12;
}

.urgency-badge.low {
  background: rgba(39, 174, 96, 0.15);
  color: #27ae60;
}

.pop-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
}

.needs-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.need-tag {
  display: inline-block;
  padding: 5px 14px;
  background: rgba(30, 58, 95, 0.3);
  border: 1px solid var(--primary);
  color: var(--text);
  font-size: 13px;
  border-radius: var(--radius-lg);
  text-transform: capitalize;
}

.no-data {
  font-size: 13px;
  color: var(--text-secondary);
}

.summary-text {
  font-size: 14px;
  color: var(--text);
  line-height: 1.7;
}

/* ── Common ── */

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

.empty-state h3 {
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

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
