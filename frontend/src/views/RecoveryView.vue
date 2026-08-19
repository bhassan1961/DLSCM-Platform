<template>
  <div class="recovery-page">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="page-header">
      <h2>{{ $t('recovery.title') }}</h2>
      <p class="page-subtitle">{{ $t('recovery.subtitle') }}</p>
    </div>

    <div class="top-bar">
      <select v-model="selectedDisaster" class="form-select" @change="fetchPlans">
        <option :value="null">{{ $t('recovery.allDisasters') }}</option>
        <option v-for="d in disasters" :key="d.id" :value="d.id">{{ d.name }}</option>
      </select>
      <button class="action-btn" @click="showCreate = true">{{ $t('recovery.newPlan') }}</button>
    </div>

    <!-- Create dialog -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal-card">
        <h3>{{ $t('recovery.createPlan') }}</h3>
        <form @submit.prevent="createPlan" class="form-stack">
          <div class="form-group">
            <label class="form-label">{{ $t('recovery.disaster') }}</label>
            <select v-model="newPlan.disaster_id" class="form-input" required>
              <option v-for="d in disasters" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('recovery.planTitle') }}</label>
            <input v-model="newPlan.title" class="form-input" :placeholder="$t('recovery.planTitlePlaceholder')" required />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('common.description') }}</label>
            <textarea v-model="newPlan.description" class="form-input" rows="3" :placeholder="$t('recovery.descriptionPlaceholder')"></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('recovery.targetCompletion') }}</label>
            <input v-model="newPlan.target_completion" class="form-input" type="date" />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showCreate = false">{{ $t('common.cancel') }}</button>
            <button type="submit" class="action-btn">{{ $t('common.create') }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && !plans.length" class="empty-state">
      <p>{{ $t('recovery.emptyState') }}</p>
    </div>

    <!-- Plans list -->
    <div v-for="plan in plans" :key="plan.id" class="plan-card">
      <div class="plan-header">
        <div>
          <h3 class="plan-title">{{ plan.title }}</h3>
          <span class="plan-meta">{{ plan.disaster_name }} &middot; {{ $t('recovery.created') }} {{ formatDate(plan.created_at) }}</span>
        </div>
        <span class="phase-badge">{{ phaseLabel(plan.current_phase) }}</span>
      </div>

      <p v-if="plan.description" class="plan-desc">{{ plan.description }}</p>

      <!-- Phase timeline -->
      <div class="phase-timeline">
        <div
          v-for="p in phases"
          :key="p.phase"
          class="phase-step"
          :class="phaseStepClass(plan, p.phase)"
          @click="openPhaseEdit(plan, p.phase)"
        >
          <div class="phase-dot"></div>
          <div class="phase-info">
            <span class="phase-name">{{ p.label }}</span>
            <span class="phase-status">{{ plan.phases[p.phase]?.status || $t('recovery.statusPending') }}</span>
          </div>
        </div>
      </div>

      <!-- Procurement section -->
      <div class="procurement-section">
        <div class="procurement-header">
          <h4>{{ $t('recovery.procurementItems') }}</h4>
          <button class="btn-small" @click="openProcurement(plan)">{{ $t('recovery.addItem') }}</button>
        </div>
        <div v-if="plan.procurement?.length" class="procurement-list">
          <div v-for="item in plan.procurement" :key="item.id" class="procurement-row">
            <span class="proc-item">{{ item.item }}</span>
            <span class="proc-cat">{{ item.category }}</span>
            <span class="proc-qty">{{ item.quantity }}</span>
            <span class="proc-cost">${{ item.total_cost?.toLocaleString() }}</span>
            <StatusBadge :status="item.status" size="sm" />
          </div>
        </div>
        <p v-else class="no-items">{{ $t('recovery.noProcurementItems') }}</p>
      </div>
    </div>

    <!-- Phase edit modal -->
    <div v-if="editingPhase" class="modal-overlay" @click.self="editingPhase = null">
      <div class="modal-card">
        <h3>{{ $t('recovery.updatePhase') }}: {{ phaseLabel(editingPhase.phase) }}</h3>
        <form @submit.prevent="updatePhase" class="form-stack">
          <div class="form-group">
            <label class="form-label">{{ $t('common.status') }}</label>
            <select v-model="editingPhase.status" class="form-input">
              <option value="pending">{{ $t('recovery.statusPending') }}</option>
              <option value="in_progress">{{ $t('recovery.statusInProgress') }}</option>
              <option value="completed">{{ $t('recovery.statusCompleted') }}</option>
              <option value="blocked">{{ $t('recovery.statusBlocked') }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('common.notes') }}</label>
            <textarea v-model="editingPhase.notes" class="form-input" rows="3" :placeholder="$t('recovery.phaseNotesPlaceholder')"></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="editingPhase = null">{{ $t('common.cancel') }}</button>
            <button type="submit" class="action-btn">{{ $t('common.update') }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Procurement modal -->
    <div v-if="procModal" class="modal-overlay" @click.self="procModal = null">
      <div class="modal-card">
        <h3>{{ $t('recovery.addProcurementItem') }}</h3>
        <form @submit.prevent="addProcurement" class="form-stack">
          <div class="form-group">
            <label class="form-label">{{ $t('recovery.itemName') }}</label>
            <input v-model="procForm.item" class="form-input" :placeholder="$t('recovery.itemNamePlaceholder')" required />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('recovery.category') }}</label>
              <select v-model="procForm.category" class="form-input">
                <option value="construction">{{ $t('recovery.catConstruction') }}</option>
                <option value="equipment">{{ $t('recovery.catEquipment') }}</option>
                <option value="medical">{{ $t('recovery.catMedical') }}</option>
                <option value="food">{{ $t('recovery.catFood') }}</option>
                <option value="water">{{ $t('recovery.catWater') }}</option>
                <option value="shelter">{{ $t('recovery.catShelter') }}</option>
                <option value="other">{{ $t('recovery.catOther') }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('common.quantity') }}</label>
              <input v-model.number="procForm.quantity" class="form-input" type="number" min="1" required />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('recovery.unitCost') }}</label>
              <input v-model.number="procForm.unit_cost" class="form-input" type="number" step="0.01" min="0" required />
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('recovery.supplier') }}</label>
              <input v-model="procForm.supplier" class="form-input" :placeholder="$t('common.optional')" />
            </div>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="procModal = null">{{ $t('common.cancel') }}</button>
            <button type="submit" class="action-btn">{{ $t('common.add') }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { recoveryApi, disastersApi } from '../api/client'
import StatusBadge from '../components/common/StatusBadge.vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { useErrorHandler } from '../composables/useErrorHandler'

const { t } = useI18n()
const { error, handleError, clearError } = useErrorHandler()

const disasters = ref([])
const plans = ref([])
const loading = ref(true)
const selectedDisaster = ref(null)
const showCreate = ref(false)
const editingPhase = ref(null)
const procModal = ref(null)

const phases = computed(() => [
  { phase: 'assessment', label: t('recovery.phaseAssessment') },
  { phase: 'stabilization', label: t('recovery.phaseStabilization') },
  { phase: 'short_term', label: t('recovery.phaseShortTerm') },
  { phase: 'long_term', label: t('recovery.phaseLongTerm') },
  { phase: 'resilience', label: t('recovery.phaseResilience') },
])

const newPlan = reactive({ disaster_id: null, title: '', description: '', target_completion: '' })
const procForm = reactive({ item: '', category: 'construction', quantity: 1, unit_cost: 0, supplier: '' })

function phaseLabel(phase) {
  return phases.value.find(p => p.phase === phase)?.label || phase
}

function phaseStepClass(plan, phase) {
  const s = plan.phases[phase]?.status
  return { completed: s === 'completed', active: s === 'in_progress', blocked: s === 'blocked' }
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString()
}

function openPhaseEdit(plan, phase) {
  editingPhase.value = {
    planId: plan.id,
    phase,
    status: plan.phases[phase]?.status || 'pending',
    notes: plan.phases[phase]?.notes || '',
  }
}

function openProcurement(plan) {
  procModal.value = plan.id
  Object.assign(procForm, { item: '', category: 'construction', quantity: 1, unit_cost: 0, supplier: '' })
}

async function fetchPlans() {
  loading.value = true
  try {
    const { data } = await recoveryApi.plans(selectedDisaster.value)
    plans.value = Array.isArray(data) ? data : []
  } catch (e) {
    handleError(e, 'Failed to load recovery plans')
  } finally {
    loading.value = false
  }
}

async function createPlan() {
  try {
    await recoveryApi.createPlan(newPlan)
    showCreate.value = false
    Object.assign(newPlan, { disaster_id: null, title: '', description: '', target_completion: '' })
    await fetchPlans()
  } catch (e) {
    handleError(e, 'Failed to create plan')
  }
}

async function updatePhase() {
  try {
    await recoveryApi.updatePhase(editingPhase.value.planId, {
      phase: editingPhase.value.phase,
      status: editingPhase.value.status,
      notes: editingPhase.value.notes,
    })
    editingPhase.value = null
    await fetchPlans()
  } catch (e) {
    handleError(e, 'Failed to update phase')
  }
}

async function addProcurement() {
  try {
    await recoveryApi.addProcurement(procModal.value, procForm)
    procModal.value = null
    await fetchPlans()
  } catch (e) {
    handleError(e, 'Failed to add procurement')
  }
}

async function loadInitialData() {
  try {
    const { data } = await disastersApi.list()
    disasters.value = Array.isArray(data) ? data : data.disasters || []
  } catch (e) { handleError(e, 'Failed to load disasters') }
  await fetchPlans()
}

function retryLoad() {
  clearError()
  loadInitialData()
}

onMounted(loadInitialData)
</script>

<style scoped>
.recovery-page { max-width: 960px; }
.page-header { margin-bottom: 24px; }
.page-header h2 { font-size: 24px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.page-subtitle { font-size: 14px; color: var(--text-secondary); }

.top-bar { display: flex; gap: 12px; margin-bottom: 24px; align-items: center; }
.form-select { padding: 8px 14px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); color: var(--text); font-size: 14px; min-width: 200px; }
.action-btn { padding: 8px 20px; border: none; border-radius: var(--radius-sm); background: var(--primary); color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; white-space: nowrap; }
.action-btn:hover { filter: brightness(1.1); }

.plan-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; margin-bottom: 16px; }
.plan-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.plan-title { font-size: 18px; font-weight: 600; color: var(--text); margin-bottom: 4px; }
.plan-meta { font-size: 12px; color: var(--text-secondary); }
.plan-desc { font-size: 14px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 16px; }

.phase-badge { font-size: 12px; font-weight: 600; padding: 4px 12px; border-radius: var(--radius); background: rgba(232,145,58,0.12); color: var(--accent); white-space: nowrap; }

/* Phase timeline */
.phase-timeline { display: flex; gap: 0; margin-bottom: 20px; border-top: 1px solid var(--border); padding-top: 16px; }
.phase-step { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8px; cursor: pointer; padding: 8px 4px; border-radius: var(--radius-sm); transition: background 0.15s; position: relative; }
.phase-step:hover { background: var(--bg); }
.phase-step::after { content: ''; position: absolute; top: 20px; left: 50%; width: 100%; height: 2px; background: var(--border); z-index: 0; }
.phase-step:last-child::after { display: none; }

.phase-dot { width: 16px; height: 16px; border-radius: 50%; border: 2px solid var(--border); background: var(--surface); z-index: 1; transition: all 0.2s; }
.phase-step.completed .phase-dot { background: var(--success); border-color: var(--success); }
.phase-step.active .phase-dot { background: var(--accent); border-color: var(--accent); box-shadow: 0 0 0 3px rgba(232,145,58,0.2); }
.phase-step.blocked .phase-dot { background: var(--danger); border-color: var(--danger); }

.phase-info { text-align: center; }
.phase-name { display: block; font-size: 11px; font-weight: 600; color: var(--text); line-height: 1.3; }
.phase-status { display: block; font-size: 10px; color: var(--text-secondary); text-transform: capitalize; }

/* Procurement */
.procurement-section { border-top: 1px solid var(--border); padding-top: 16px; }
.procurement-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.procurement-header h4 { font-size: 14px; font-weight: 600; color: var(--text); }
.btn-small { padding: 4px 12px; border: 1px solid var(--primary); border-radius: var(--radius-sm); background: transparent; color: var(--primary); font-size: 12px; font-weight: 600; cursor: pointer; }
.btn-small:hover { background: var(--primary); color: #fff; }

.procurement-list { display: flex; flex-direction: column; gap: 6px; }
.procurement-row { display: flex; align-items: center; gap: 12px; padding: 8px 12px; background: var(--bg); border-radius: var(--radius-sm); font-size: 13px; }
.proc-item { flex: 1; font-weight: 500; color: var(--text); }
.proc-cat { width: 100px; color: var(--text-secondary); text-transform: capitalize; }
.proc-qty { width: 60px; text-align: right; color: var(--text); font-variant-numeric: tabular-nums; }
.proc-cost { width: 100px; text-align: right; font-weight: 600; color: var(--text); font-variant-numeric: tabular-nums; }
.no-items { font-size: 13px; color: var(--text-secondary); }

/* Modals */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-card { background: var(--surface); border-radius: var(--radius); padding: 28px; width: 90vw; max-width: 480px; }
.modal-card h3 { font-size: 18px; font-weight: 600; color: var(--text); margin-bottom: 20px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.btn-secondary { padding: 8px 20px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: transparent; color: var(--text-secondary); font-size: 14px; cursor: pointer; }

.form-stack { display: flex; flex-direction: column; gap: 14px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.form-group { display: flex; flex-direction: column; }
.form-label { font-size: 12px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.form-input { padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); color: var(--text); font-size: 14px; }
.form-input:focus { outline: none; border-color: var(--primary); }
textarea.form-input { resize: vertical; font-family: inherit; }

.empty-state { display: flex; align-items: center; justify-content: center; padding: 64px 24px; color: var(--text-secondary); }

@media (max-width: 640px) {
  .phase-timeline { flex-direction: column; gap: 8px; }
  .phase-step { flex-direction: row; gap: 12px; }
  .phase-step::after { display: none; }
  .phase-info { text-align: left; }
  .form-row { grid-template-columns: 1fr; }
  .procurement-row { flex-wrap: wrap; }
}
</style>
