<template>
  <div class="simulation">
    <div class="page-header">
      <h2>Scenario Simulation</h2>
      <p class="page-subtitle">Model disaster scenarios and assess supply chain readiness</p>
    </div>

    <div class="sim-layout">
      <!-- Scenario Builder -->
      <div class="builder-panel">
        <div class="panel-card">
          <h3 class="panel-title">Scenario Builder</h3>
          <form @submit.prevent="runSimulation" class="builder-form">
            <div class="form-group">
              <label>Scenario Name</label>
              <input v-model="form.name" type="text" placeholder="e.g. Nepal Earthquake 2025" required />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Disaster Type</label>
                <select v-model="form.disaster_type" required>
                  <option value="" disabled>Select type</option>
                  <option v-for="t in disasterTypes" :key="t" :value="t">
                    {{ t.charAt(0).toUpperCase() + t.slice(1) }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>Severity</label>
                <select v-model="form.severity" required>
                  <option value="" disabled>Select severity</option>
                  <option v-for="s in severities" :key="s" :value="s">
                    {{ s.charAt(0).toUpperCase() + s.slice(1) }}
                  </option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label>Country</label>
              <input v-model="form.country" type="text" placeholder="e.g. Nepal" required />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Latitude</label>
                <input v-model.number="form.latitude" type="number" step="0.01" placeholder="27.7" required />
              </div>
              <div class="form-group">
                <label>Longitude</label>
                <input v-model.number="form.longitude" type="number" step="0.01" placeholder="85.3" required />
              </div>
            </div>
            <div class="form-group">
              <label>Affected Population</label>
              <input v-model.number="form.affected_population" type="number" min="0" placeholder="500000" required />
            </div>
            <button type="submit" class="run-btn" :disabled="running">
              <span v-if="running" class="spinner-sm"></span>
              {{ running ? 'Running...' : 'Run Simulation' }}
            </button>
            <p v-if="runError" class="form-error">{{ runError }}</p>
          </form>
        </div>
      </div>

      <!-- Results -->
      <div class="results-panel">
        <div v-if="!result && !running" class="empty-results">
          <p>Configure a scenario and run a simulation to see results here.</p>
        </div>

        <div v-if="running" class="loading-state">
          <div class="spinner"></div>
          <span>Running simulation...</span>
        </div>

        <template v-if="result && !running">
          <!-- Summary Cards -->
          <div class="summary-cards">
            <div class="summary-card">
              <div class="summary-value">{{ result.estimated_response_hours?.toFixed(1) }}</div>
              <div class="summary-label">Response Time (hrs)</div>
            </div>
            <div class="summary-card">
              <div class="summary-value">{{ result.nearest_warehouse_km?.toLocaleString() }}</div>
              <div class="summary-label">Nearest Warehouse (km)</div>
            </div>
            <div class="summary-card">
              <div class="summary-value accent">{{ result.readiness_score?.toFixed(0) }}%</div>
              <div class="summary-label">Readiness Score</div>
            </div>
            <div class="summary-card">
              <div class="summary-value">{{ formatCost(result.estimated_cost_usd) }}</div>
              <div class="summary-label">Estimated Cost (USD)</div>
            </div>
          </div>

          <!-- Damage Assessment -->
          <div v-if="result.damage_assessment" class="panel-card">
            <h3 class="panel-title">
              Damage Assessment
              <span class="overall-score">Overall: {{ result.damage_assessment.overall_index?.toFixed(1) }}</span>
            </h3>
            <div class="bar-chart">
              <div v-for="sector in damageSectors" :key="sector.key" class="bar-container">
                <div class="bar-label">{{ sector.label }}</div>
                <div class="bar-track">
                  <div
                    class="bar-fill"
                    :style="{ width: (result.damage_assessment[sector.key] || 0) + '%', background: barColor(result.damage_assessment[sector.key]) }"
                  ></div>
                </div>
                <div class="bar-value">{{ result.damage_assessment[sector.key] || 0 }}</div>
              </div>
            </div>
          </div>

          <!-- Demand Forecast -->
          <div v-if="result.demand_forecast" class="panel-card">
            <h3 class="panel-title">Demand Forecast</h3>
            <div class="forecast-grid">
              <div v-for="(val, key) in result.demand_forecast" :key="key" class="forecast-item">
                <div class="forecast-category">{{ formatCategory(key) }}</div>
                <div class="forecast-total">{{ val.total?.toLocaleString() }} <span class="forecast-unit">{{ val.unit }}</span></div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Saved Scenarios -->
    <div class="scenarios-section">
      <h3 class="section-title">Saved Scenarios</h3>
      <DataTable :columns="scenarioColumns" :rows="scenarios" :loading="scenariosLoading" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { simulationApi } from '../api/client'
import DataTable from '../components/common/DataTable.vue'

const disasterTypes = ['earthquake', 'flood', 'hurricane', 'drought', 'conflict', 'epidemic']
const severities = ['minor', 'moderate', 'major', 'catastrophic']
const damageSectors = [
  { key: 'infrastructure', label: 'Infrastructure' },
  { key: 'housing', label: 'Housing' },
  { key: 'health', label: 'Health' },
  { key: 'education', label: 'Education' },
  { key: 'agriculture', label: 'Agriculture' }
]

const form = ref({
  name: '',
  disaster_type: '',
  severity: '',
  country: '',
  latitude: null,
  longitude: null,
  affected_population: null
})

const running = ref(false)
const runError = ref('')
const result = ref(null)

const scenarios = ref([])
const scenariosLoading = ref(true)

const scenarioColumns = [
  { key: 'name', label: 'Scenario', sortable: true },
  { key: 'disaster_type', label: 'Type', sortable: true },
  { key: 'severity', label: 'Severity', sortable: true },
  { key: 'country', label: 'Country', sortable: true },
  { key: 'affected_population', label: 'Population', sortable: true },
  { key: 'status', label: 'Status', sortable: true }
]

function barColor(score) {
  if (score >= 70) return 'var(--danger)'
  if (score >= 40) return 'var(--warning)'
  return 'var(--success)'
}

function formatCost(value) {
  if (value == null) return '-'
  if (value >= 1e6) return '$' + (value / 1e6).toFixed(1) + 'M'
  if (value >= 1e3) return '$' + (value / 1e3).toFixed(0) + 'K'
  return '$' + value.toLocaleString()
}

function formatCategory(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

async function runSimulation() {
  running.value = true
  runError.value = ''
  result.value = null
  try {
    const { data } = await simulationApi.run(form.value)
    const da = data.damage_assessment || {}
    result.value = {
      ...data,
      estimated_cost_usd: data.estimated_response_cost_usd ?? data.estimated_cost_usd,
      damage_assessment: {
        ...da,
        overall_index: da.overall_damage_index ?? da.overall_index,
        infrastructure: da.sector_scores?.infrastructure ?? da.infrastructure ?? 0,
        housing: da.sector_scores?.housing ?? da.housing ?? 0,
        health: da.sector_scores?.health ?? da.health ?? 0,
        education: da.sector_scores?.education ?? da.education ?? 0,
        agriculture: da.sector_scores?.agriculture ?? da.agriculture ?? 0,
      },
    }
    // Refresh scenarios list
    fetchScenarios()
  } catch (e) {
    console.error('Simulation failed:', e)
    runError.value = e.response?.data?.detail || 'Simulation failed. Please try again.'
  } finally {
    running.value = false
  }
}

async function fetchScenarios() {
  scenariosLoading.value = true
  try {
    const { data } = await simulationApi.scenarios()
    scenarios.value = Array.isArray(data) ? data : data.scenarios || []
  } catch (e) {
    console.error('Failed to load scenarios:', e)
    scenarios.value = []
  } finally {
    scenariosLoading.value = false
  }
}

onMounted(fetchScenarios)
</script>

<style scoped>
.simulation {
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

.sim-layout {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 24px;
  margin-bottom: 32px;
}

@media (max-width: 900px) {
  .sim-layout {
    grid-template-columns: 1fr;
  }
}

.panel-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.overall-score {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.builder-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.form-group input,
.form-group select {
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  transition: border-color 0.15s ease;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary);
}

.form-group input::placeholder {
  color: var(--text-secondary);
  opacity: 0.6;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.run-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  background: var(--primary);
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease;
  margin-top: 4px;
}

.run-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.run-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-error {
  font-size: 13px;
  color: var(--danger);
}

.empty-results {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 40px;
  color: var(--text-secondary);
  text-align: center;
  font-size: 14px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.summary-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.summary-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 4px;
}

.summary-value.accent {
  color: var(--accent);
}

.summary-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

/* Bar chart */
.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bar-container {
  display: grid;
  grid-template-columns: 120px 1fr 40px;
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
  height: 24px;
  background: var(--bg);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}

.bar-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

/* Forecast */
.forecast-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.forecast-item {
  background: var(--bg);
  border-radius: 6px;
  padding: 12px;
}

.forecast-category {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 4px;
}

.forecast-total {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
}

.forecast-unit {
  font-size: 12px;
  font-weight: 400;
  color: var(--text-secondary);
}

/* Scenarios section */
.scenarios-section {
  margin-top: 8px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 12px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
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

.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
