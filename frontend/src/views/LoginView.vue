<template>
  <div class="login-page">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">{{ $t('auth.platformTitle') }}</h1>
        <p class="login-subtitle">{{ $t('auth.platformSubtitle') }}</p>
      </div>

      <!-- Tab toggle -->
      <div class="login-tabs">
        <button class="tab-btn" :class="{ active: mode === 'demo' }" @click="mode = 'demo'">{{ $t('auth.demoLogin') }}</button>
        <button class="tab-btn" :class="{ active: mode === 'credentials' }" @click="mode = 'credentials'">{{ $t('auth.signIn') }}</button>
      </div>

      <!-- Demo user picker -->
      <div v-if="mode === 'demo'">
        <div v-if="loading" class="login-loading">
          <div class="spinner"></div>
          <span>{{ $t('common.loadingUsers') }}</span>
        </div>

        <div v-else-if="error" class="login-error">
          <p>{{ error }}</p>
          <button class="retry-btn" @click="fetchUsers">{{ $t('common.retry') }}</button>
        </div>

        <div v-else class="users-list">
          <p class="users-prompt">{{ $t('auth.selectDemo') }}</p>
          <div
            v-for="u in users"
            :key="u.email"
            class="user-card"
            @click="handleDemoLogin(u)"
          >
            <div class="user-avatar">{{ initials(u.name) }}</div>
            <div class="user-details">
              <div class="user-name">{{ u.name }}</div>
              <div class="user-meta">
                <span class="user-role">{{ u.role }}</span>
                <span class="user-org">{{ u.organization?.name || '' }}</span>
              </div>
            </div>
            <span class="arrow">&#x2192;</span>
          </div>
        </div>
      </div>

      <!-- Credential login -->
      <div v-if="mode === 'credentials'" class="credentials-form">
        <form @submit.prevent="handleCredentialLogin">
          <div class="form-group">
            <label class="form-label" for="email">{{ $t('auth.email') }}</label>
            <input id="email" v-model="email" type="email" class="form-input" :placeholder="$t('auth.emailPlaceholder')" required />
          </div>
          <div class="form-group">
            <label class="form-label" for="password">{{ $t('auth.password') }}</label>
            <input id="password" v-model="password" type="password" class="form-input" :placeholder="$t('auth.passwordPlaceholder')" />
          </div>
          <div v-if="credError" class="field-error">{{ credError }}</div>
          <button type="submit" class="submit-btn" :disabled="submitting">
            <span v-if="submitting" class="btn-spinner"></span>
            {{ submitting ? $t('auth.signingIn') : $t('auth.signIn') }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { useAuthStore } from '../stores/auth'
import { authApi } from '../api/client'
import { useErrorHandler } from '../composables/useErrorHandler'

const router = useRouter()
const auth = useAuthStore()

const { error, handleError, clearError } = useErrorHandler()

const mode = ref('demo')
const users = ref([])
const loading = ref(true)

const email = ref('')
const password = ref('')
const credError = ref(null)
const submitting = ref(false)

function initials(name) {
  return name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || '??'
}

async function fetchUsers() {
  loading.value = true
  clearError()
  try {
    const { data } = await authApi.listUsers()
    users.value = data.users || data || []
  } catch (e) {
    handleError(e, 'Failed to load demo users. Is the backend running?')
  } finally {
    loading.value = false
  }
}

async function handleDemoLogin(user) {
  try {
    await auth.login(user.email)
    router.push('/app/dashboard')
  } catch (e) {
    handleError(e, 'Login failed. Please try again.')
  }
}

async function handleCredentialLogin() {
  credError.value = null
  submitting.value = true
  try {
    await auth.login(email.value, password.value || undefined)
    router.push('/app/dashboard')
  } catch (e) {
    credError.value = e.response?.data?.detail || 'Login failed. Check your credentials.'
  } finally {
    submitting.value = false
  }
}

function retryLoad() {
  clearError()
  fetchUsers()
}

onMounted(fetchUsers)
</script>

<style scoped>
.login-page {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  padding: 24px;
}

.login-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  width: 100%;
  max-width: 480px;
  padding: 40px;
}

.login-header {
  text-align: center;
  margin-bottom: 24px;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: 2px;
}

.login-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 8px;
}

.login-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

.tab-btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  background: var(--bg);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.tab-btn.active {
  background: var(--primary);
  color: #ffffff;
}

.users-prompt {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.users-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: var(--shadow-sm);
}

.user-card:hover {
  border-color: var(--accent);
  background: var(--surface-raised);
  box-shadow: var(--shadow);
  transform: translateY(-1px);
}

.user-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.user-details { flex: 1; min-width: 0; }

.user-name { font-weight: 600; font-size: 15px; color: var(--text); }

.user-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 3px;
}

.user-role {
  background: rgba(232, 145, 58, 0.1);
  color: var(--accent);
  padding: 1px 8px;
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.arrow {
  color: var(--text-secondary);
  font-size: 18px;
  transition: transform 0.15s ease;
}

.user-card:hover .arrow {
  transform: translateX(3px);
  color: var(--accent);
}

.credentials-form {
  display: flex;
  flex-direction: column;
}

.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text);
  font-size: 14px;
  transition: border-color 0.15s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(30, 58, 95, 0.1);
}

.field-error {
  color: var(--danger);
  font-size: 13px;
  margin-bottom: 12px;
}

.submit-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border: none;
  border-radius: var(--radius);
  background: var(--primary);
  color: #ffffff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.submit-btn:hover:not(:disabled) { filter: brightness(1.1); }
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.login-loading, .login-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px;
  color: var(--text-secondary);
}

.login-error { color: var(--danger); }

.retry-btn {
  padding: 8px 20px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.retry-btn:hover { background: var(--bg); border-color: var(--accent); }

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 500px) {
  .login-card { padding: 28px 20px; }
  .login-title { font-size: 24px; }
}
</style>
