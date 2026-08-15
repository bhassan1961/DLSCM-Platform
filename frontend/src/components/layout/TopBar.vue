<template>
  <header class="topbar">
    <div class="topbar-left">
      <h1 class="page-title">{{ route.meta.title || 'DLSCM' }}</h1>
      <span v-if="route.meta.phase" class="phase-badge">Phase {{ route.meta.phase }}</span>
    </div>
    <div class="topbar-right">
      <button class="notification-btn" title="Notifications">
        <span class="bell-icon">&#x1F514;</span>
        <span v-if="notifications.items.length" class="notif-count">{{ notifications.items.length }}</span>
      </button>
      <div v-if="auth.isLoggedIn" class="user-info">
        <span class="user-name">{{ auth.user?.name || 'User' }}</span>
        <span class="user-org">{{ auth.user?.organization?.name || '' }}</span>
      </div>
      <button v-if="auth.isLoggedIn" class="logout-btn" @click="handleLogout">
        Logout
      </button>
    </div>
  </header>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useNotificationsStore } from '../../stores/notifications'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const notifications = useNotificationsStore()

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 60px;
  min-height: 60px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text);
}

.phase-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 12px;
  background: var(--primary);
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.notification-btn {
  position: relative;
  background: none;
  border: none;
  font-size: 20px;
  padding: 4px;
  line-height: 1;
}

.bell-icon {
  font-size: 20px;
}

.notif-count {
  position: absolute;
  top: -2px;
  right: -6px;
  background: var(--danger);
  color: #ffffff;
  font-size: 10px;
  font-weight: 700;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  line-height: 1.3;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.user-org {
  font-size: 11px;
  color: var(--text-secondary);
}

.logout-btn {
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 13px;
  transition: all 0.15s ease;
}

.logout-btn:hover {
  border-color: var(--danger);
  color: var(--danger);
}
</style>
