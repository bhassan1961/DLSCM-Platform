<template>
  <div class="after-action-view">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="page-header">
      <div>
        <h2>{{ $t('nav.afterAction') }}</h2>
        <p class="subtitle">Post-response performance analysis and lessons learned</p>
      </div>
    </div>

    <div class="controls-bar">
      <div class="control-group">
        <label class="control-label">Disaster</label>
        <select v-model="selectedDisaster" class="control-select" @change="loadReviews">
          <option :value="null" disabled>Select a disaster...</option>
          <option v-for="d in disasters" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
      </div>
      <button v-if="selectedDisaster" class="btn-primary" @click="showCreate = true">+ New Review</button>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Loading reviews...</span>
    </div>

    <div v-if="!loading && !selectedDisaster" class="empty-state">
      <svg class="empty-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" /></svg>
      <h3>Select a disaster to view after-action reviews</h3>
      <p>Performance analysis and lessons learned will appear here.</p>
    </div>

    <div v-if="!loading && selectedDisaster && !reviews.length" class="empty-state">
      <svg class="empty-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" /></svg>
      <h3>No reviews available</h3>
      <p>No after-action reviews have been conducted for this disaster yet.</p>
    </div>

    <div v-if="reviews.length && !loading" class="reviews-list">
      <div v-for="review in reviews" :key="review.id" class="review-card">
        <div class="review-header">
          <h3>{{ review.title }}</h3>
          <div class="review-score" :class="scoreClass(review.overall_score)">
            {{ review.overall_score ?? '-' }}<span class="score-label">/100</span>
          </div>
        </div>

        <div class="review-date">Reviewed: {{ formatDate(review.review_date) }}</div>

        <div class="metrics-row">
          <div class="metric">
            <div class="metric-value">{{ review.response_time_hours ?? '-' }}h</div>
            <div class="metric-label">Response Time</div>
          </div>
          <div class="metric">
            <div class="metric-value">${{ review.cost_per_beneficiary?.toFixed(2) ?? '-' }}</div>
            <div class="metric-label">Cost/Beneficiary</div>
          </div>
          <div class="metric">
            <div class="metric-value">{{ review.stockout_events ?? 0 }}</div>
            <div class="metric-label">Stockout Events</div>
          </div>
        </div>

        <div class="review-section">
          <h4>Lessons Learned</h4>
          <p>{{ review.lessons_learned || 'None recorded.' }}</p>
        </div>

        <div class="review-section">
          <h4>Recommendations</h4>
          <p>{{ review.recommendations || 'None recorded.' }}</p>
        </div>
      </div>
    </div>

    <!-- Create Review Modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="aar-modal-title" @keydown.escape="showCreate = false">
        <div class="modal-header">
          <h3 id="aar-modal-title">New After-Action Review</h3>
          <button class="modal-close" @click="showCreate = false" aria-label="Close">&times;</button>
        </div>
        <form @submit.prevent="createReview" class="modal-body">
          <div class="form-group">
            <label for="aar-title">Title</label>
            <input id="aar-title" v-model="reviewForm.title" required placeholder="e.g. Turkana Drought Response Review" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="aar-score">Overall Score (0-100)</label>
              <input id="aar-score" type="number" min="0" max="100" v-model.number="reviewForm.overall_score" required />
            </div>
            <div class="form-group">
              <label for="aar-response">Response Time (hours)</label>
              <input id="aar-response" type="number" v-model.number="reviewForm.response_time_hours" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="aar-cost">Cost per Beneficiary ($)</label>
              <input id="aar-cost" type="number" step="0.01" v-model.number="reviewForm.cost_per_beneficiary" />
            </div>
            <div class="form-group">
              <label for="aar-stockout">Stockout Events</label>
              <input id="aar-stockout" type="number" v-model.number="reviewForm.stockout_events" />
            </div>
          </div>
          <div class="form-group">
            <label for="aar-lessons">Lessons Learned</label>
            <textarea id="aar-lessons" v-model="reviewForm.lessons_learned" rows="3" placeholder="Key findings and takeaways..."></textarea>
          </div>
          <div class="form-group">
            <label for="aar-recs">Recommendations</label>
            <textarea id="aar-recs" v-model="reviewForm.recommendations" rows="3" placeholder="Recommended improvements..."></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showCreate = false">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="creating">{{ creating ? 'Saving...' : 'Submit Review' }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { disastersApi, afterActionApi } from '../api/client'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const disasters = ref([])
const selectedDisaster = ref(null)
const reviews = ref([])
const loading = ref(false)
const showCreate = ref(false)
const creating = ref(false)
const reviewForm = ref({
  title: '',
  overall_score: 70,
  response_time_hours: null,
  cost_per_beneficiary: null,
  stockout_events: 0,
  lessons_learned: '',
  recommendations: ''
})

function scoreClass(score) {
  if (score == null) return ''
  if (score >= 75) return 'score-good'
  if (score >= 50) return 'score-fair'
  return 'score-poor'
}

function formatDate(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
}

async function createReview() {
  creating.value = true
  try {
    await afterActionApi.create({ ...reviewForm.value, disaster_id: selectedDisaster.value })
    showCreate.value = false
    reviewForm.value = { title: '', overall_score: 70, response_time_hours: null, cost_per_beneficiary: null, stockout_events: 0, lessons_learned: '', recommendations: '' }
    await loadReviews()
  } catch (e) {
    handleError(e, 'Failed to create review')
  } finally {
    creating.value = false
  }
}

async function loadReviews() {
  if (!selectedDisaster.value) return
  loading.value = true
  reviews.value = []
  try {
    const { data } = await afterActionApi.list(selectedDisaster.value)
    reviews.value = Array.isArray(data) ? data : (data.reviews || [])
  } catch (e) {
    handleError(e, 'Failed to load reviews')
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
.after-action-view {
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
  gap: 24px;
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
  min-width: 260px;
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

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
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

.reviews-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.review-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
}

.review-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.review-header h3 {
  font-size: 17px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.review-score {
  font-size: 28px;
  font-weight: 700;
  min-width: 80px;
  text-align: right;
}

.score-label {
  font-size: 14px;
  font-weight: 400;
  color: var(--text-secondary);
}

.score-good { color: var(--success); }
.score-fair { color: var(--warning); }
.score-poor { color: var(--danger); }

.review-date {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.metrics-row {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: var(--bg);
  border-radius: var(--radius-sm);
}

.metric {
  text-align: center;
  flex: 1;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
}

.metric-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.review-section {
  margin-top: 16px;
}

.review-section h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 8px;
}

.review-section p {
  font-size: 14px;
  color: var(--text);
  line-height: 1.6;
  margin: 0;
}

.btn-primary {
  padding: 8px 16px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}
.btn-primary:hover { opacity: 0.9; }
.btn-primary:disabled { opacity: 0.5; cursor: default; }

.btn-secondary {
  padding: 8px 16px;
  background: var(--surface);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  width: 90%;
  max-width: 540px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg, 0 8px 32px rgba(0,0,0,0.3));
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--text-secondary);
  cursor: pointer;
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
  font-family: inherit;
}

.form-row {
  display: flex;
  gap: 12px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 8px;
}

@media (max-width: 600px) {
  .form-row { flex-direction: column; }
}
</style>
