<template>
  <div class="edxl-page">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="page-header">
      <h2>{{ $t('edxl.title') }}</h2>
      <p class="page-subtitle">{{ $t('edxl.subtitle') }}</p>
    </div>

    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'generate' }" @click="tab = 'generate'">{{ $t('edxl.generateCap') }}</button>
      <button class="tab" :class="{ active: tab === 'wrap' }" @click="tab = 'wrap'">{{ $t('edxl.wrapEdxl') }}</button>
      <button class="tab" :class="{ active: tab === 'parse' }" @click="tab = 'parse'">{{ $t('edxl.parseMessage') }}</button>
    </div>

    <!-- Generate CAP -->
    <div v-if="tab === 'generate'" class="panel">
      <form @submit.prevent="generateCap" class="form-grid">
        <div class="form-group span-2">
          <label class="form-label">{{ $t('edxl.alertTitle') }}</label>
          <input v-model="capForm.title" class="form-input" :placeholder="$t('edxl.alertTitlePlaceholder')" required />
        </div>
        <div class="form-group span-2">
          <label class="form-label">{{ $t('edxl.description') }}</label>
          <textarea v-model="capForm.description" class="form-textarea" rows="3" :placeholder="$t('edxl.descriptionPlaceholder')" required></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">{{ $t('edxl.severity') }}</label>
          <select v-model="capForm.severity" class="form-input">
            <option value="minor">{{ $t('edxl.severityMinor') }}</option>
            <option value="moderate">{{ $t('edxl.severityModerate') }}</option>
            <option value="severe">{{ $t('edxl.severitySevere') }}</option>
            <option value="extreme">{{ $t('edxl.severityExtreme') }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">{{ $t('edxl.urgency') }}</label>
          <select v-model="capForm.urgency" class="form-input">
            <option value="Immediate">{{ $t('edxl.urgencyImmediate') }}</option>
            <option value="Expected">{{ $t('edxl.urgencyExpected') }}</option>
            <option value="Future">{{ $t('edxl.urgencyFuture') }}</option>
            <option value="Past">{{ $t('edxl.urgencyPast') }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">{{ $t('edxl.latitude') }}</label>
          <input v-model.number="capForm.latitude" class="form-input" type="number" step="0.0001" :placeholder="$t('edxl.latitudePlaceholder')" />
        </div>
        <div class="form-group">
          <label class="form-label">{{ $t('edxl.longitude') }}</label>
          <input v-model.number="capForm.longitude" class="form-input" type="number" step="0.0001" :placeholder="$t('edxl.longitudePlaceholder')" />
        </div>
        <div class="form-group span-2 action-row">
          <button type="submit" class="action-btn" :disabled="generating">
            {{ generating ? $t('edxl.generating') : $t('edxl.generateCap') }}
          </button>
        </div>
      </form>

      <div v-if="capResult" class="result-section">
        <h4>{{ $t('edxl.generatedCapXml') }}</h4>
        <pre class="xml-output">{{ capResult }}</pre>
      </div>
    </div>

    <!-- Wrap EDXL -->
    <div v-if="tab === 'wrap'" class="panel">
      <form @submit.prevent="wrapEdxl" class="form-grid">
        <div class="form-group span-2">
          <label class="form-label">{{ $t('edxl.xmlContentToWrap') }}</label>
          <textarea v-model="wrapForm.content_xml" class="form-textarea code" rows="6" :placeholder="$t('edxl.xmlContentPlaceholder')" required></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">{{ $t('edxl.distributionType') }}</label>
          <select v-model="wrapForm.distribution_type" class="form-input">
            <option value="Alert">{{ $t('edxl.distAlert') }}</option>
            <option value="Report">{{ $t('edxl.distReport') }}</option>
            <option value="Update">{{ $t('edxl.distUpdate') }}</option>
            <option value="Request">{{ $t('edxl.distRequest') }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">{{ $t('edxl.keywords') }}</label>
          <input v-model="wrapForm.keywordsStr" class="form-input" :placeholder="$t('edxl.keywordsPlaceholder')" />
        </div>
        <div class="form-group span-2 action-row">
          <button type="submit" class="action-btn" :disabled="wrapping">
            {{ wrapping ? $t('edxl.wrapping') : $t('edxl.wrapEdxl') }}
          </button>
        </div>
      </form>

      <div v-if="wrapResult" class="result-section">
        <h4>{{ $t('edxl.edxlEnvelope') }}</h4>
        <pre class="xml-output">{{ wrapResult }}</pre>
      </div>
    </div>

    <!-- Parse -->
    <div v-if="tab === 'parse'" class="panel">
      <form @submit.prevent="parseMessage" class="form-grid">
        <div class="form-group span-2">
          <label class="form-label">{{ $t('edxl.pasteXml') }}</label>
          <textarea v-model="parseInput" class="form-textarea code" rows="8" :placeholder="$t('edxl.pasteXmlPlaceholder')" required></textarea>
        </div>
        <div class="form-group span-2 action-row">
          <button type="submit" class="action-btn" :disabled="parsing">
            {{ parsing ? $t('edxl.parsing') : $t('edxl.parseMessage') }}
          </button>
        </div>
      </form>

      <div v-if="parseResult" class="result-section">
        <h4>{{ $t('edxl.parsedResult') }}</h4>
        <div class="parsed-fields">
          <div v-for="(value, key) in flattenResult(parseResult)" :key="key" class="parsed-row">
            <span class="parsed-key">{{ key }}</span>
            <span class="parsed-value">{{ value }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { edxlApi } from '../api/client'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const { t } = useI18n()

const tab = ref('generate')
const errorMsg = ref(null)

const capForm = reactive({ title: '', description: '', severity: 'moderate', urgency: 'Immediate', latitude: null, longitude: null })
const capResult = ref(null)
const generating = ref(false)

const wrapForm = reactive({ content_xml: '', distribution_type: 'Report', keywordsStr: '' })
const wrapResult = ref(null)
const wrapping = ref(false)

const parseInput = ref('')
const parseResult = ref(null)
const parsing = ref(false)

async function generateCap() {
  generating.value = true; errorMsg.value = null; capResult.value = null
  try {
    const { data } = await edxlApi.capGenerate(capForm)
    capResult.value = data.xml
  } catch (e) { errorMsg.value = e.response?.data?.detail || t('edxl.generationFailed') }
  finally { generating.value = false }
}

async function wrapEdxl() {
  wrapping.value = true; errorMsg.value = null; wrapResult.value = null
  try {
    const payload = {
      content_xml: wrapForm.content_xml,
      distribution_type: wrapForm.distribution_type,
      keywords: wrapForm.keywordsStr ? wrapForm.keywordsStr.split(',').map(k => k.trim()) : [],
    }
    const { data } = await edxlApi.wrapSitrep(payload)
    wrapResult.value = data.edxl_xml
  } catch (e) { errorMsg.value = e.response?.data?.detail || t('edxl.wrappingFailed') }
  finally { wrapping.value = false }
}

async function parseMessage() {
  parsing.value = true; errorMsg.value = null; parseResult.value = null
  try {
    const { data } = await edxlApi.parse(parseInput.value)
    parseResult.value = data
  } catch (e) { errorMsg.value = e.response?.data?.detail || t('edxl.parsingFailed') }
  finally { parsing.value = false }
}

function retryLoad() {
  window.location.reload()
}

function flattenResult(obj, prefix = '') {
  const flat = {}
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      Object.assign(flat, flattenResult(v, key))
    } else {
      flat[key] = v
    }
  }
  return flat
}
</script>

<style scoped>
.edxl-page { max-width: 900px; }
.page-header { margin-bottom: 24px; }
.page-header h2 { font-size: 24px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.page-subtitle { font-size: 14px; color: var(--text-secondary); }

.tabs { display: flex; gap: 0; margin-bottom: 24px; border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.tab { flex: 1; padding: 10px; border: none; background: var(--bg); color: var(--text-secondary); font-size: 13px; font-weight: 600; cursor: pointer; }
.tab.active { background: var(--primary); color: #fff; }

.panel { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.span-2 { grid-column: span 2; }
.form-label { display: block; font-size: 12px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.form-input, .form-textarea { width: 100%; padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); color: var(--text); font-size: 14px; }
.form-textarea { resize: vertical; font-family: inherit; }
.form-textarea.code { font-family: 'Consolas', 'Monaco', monospace; font-size: 12px; }
.form-input:focus, .form-textarea:focus { outline: none; border-color: var(--primary); }

.action-row { display: flex; justify-content: flex-end; }
.action-btn { padding: 10px 24px; border: none; border-radius: var(--radius-sm); background: var(--primary); color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; }
.action-btn:hover:not(:disabled) { filter: brightness(1.1); }
.action-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.result-section { margin-top: 24px; border-top: 1px solid var(--border); padding-top: 20px; }
.result-section h4 { font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 12px; }

.xml-output {
  background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 16px; font-family: 'Consolas', 'Monaco', monospace; font-size: 12px;
  color: var(--text); overflow-x: auto; white-space: pre-wrap; word-break: break-all;
  max-height: 400px; overflow-y: auto; line-height: 1.5;
}

.parsed-fields { display: flex; flex-direction: column; gap: 4px; }
.parsed-row { display: flex; gap: 12px; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
.parsed-key { font-weight: 600; color: var(--primary); min-width: 180px; flex-shrink: 0; font-family: monospace; font-size: 12px; }
.parsed-value { color: var(--text); word-break: break-word; }

.error-banner { margin-top: 16px; background: rgba(231,76,60,0.1); border: 1px solid var(--danger); border-radius: var(--radius); padding: 12px 20px; color: var(--danger); font-size: 14px; }

@media (max-width: 640px) { .form-grid { grid-template-columns: 1fr; } .span-2 { grid-column: span 1; } }
</style>
