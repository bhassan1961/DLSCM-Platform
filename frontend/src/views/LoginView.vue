<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">DLSCM Platform</h1>
        <p class="login-subtitle">Disaster Logistics &amp; Supply Chain Management</p>
      </div>

      <div v-if="loading" class="login-loading">
        <div class="spinner"></div>
        <span>Loading users...</span>
      </div>

      <div v-else-if="error" class="login-error">
        <p>{{ error }}</p>
        <button class="retry-btn" @click="fetchUsers">Retry</button>
      </div>

      <div v-else class="users-list">
        <p class="users-prompt">Select a demo account to continue:</p>
        <div
          v-for="u in users"
          :key="u.email"
          class="user-card"
          @click="handleLogin(u)"
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { authApi } from '../api/client'

const router = useRouter()
const auth = useAuthStore()

const users = ref([])
const loading = ref(true)
const error = ref(null)

function initials(name) {
  return name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || '??'
}

async function fetchUsers() {
  loading.value = true
  error.value = null
  try {
    const { data } = await authApi.listUsers()
    users.value = data.users || data || []
  } catch (e) {
    error.value = 'Failed to load demo users. Is the backend running?'
  } finally {
    loading.value = false
  }
}

async function handleLogin(user) {
  try {
    await auth.login(user.email)
    router.push('/app/dashboard')
  } catch (e) {
    error.value = 'Login failed. Please try again.'
  }
}

onMounted(fetchUsers)
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  padding: 24px;
}

.login-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 4px 24px var(--shadow);
  width: 100%;
  max-width: 480px;
  padding: 40px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
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

.users-prompt {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.users-list {
  display: flex;
  flex-direction: column;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: 12px;
}

.user-card:hover {
  border-color: var(--primary);
  background: var(--bg);
}

.user-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--primary);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.user-details {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  font-size: 15px;
  color: var(--text);
}

.user-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.user-role {
  background: rgba(30, 58, 95, 0.08);
  padding: 1px 6px;
  border-radius: 4px;
}

.arrow {
  color: var(--text-secondary);
  font-size: 18px;
}

.login-loading,
.login-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px;
  color: var(--text-secondary);
}

.login-error {
  color: var(--danger);
}

.retry-btn {
  padding: 8px 20px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--text);
  font-size: 14px;
}

.retry-btn:hover {
  background: var(--bg);
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
