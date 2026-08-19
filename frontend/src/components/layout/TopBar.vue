<template>
  <header class="topbar">
    <div class="topbar-left">
      <button
        v-if="showHamburger"
        class="hamburger-btn"
        :aria-label="$t('topbar.toggleNav')"
        @click="$emit('toggle-sidebar')"
      >
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
      </button>
      <h1 class="page-title">{{ route.meta.title || 'DLSCM' }}</h1>
      <span v-if="route.meta.phase" class="phase-badge">Phase {{ route.meta.phase }}</span>
    </div>
    <div class="topbar-right">
      <button class="icon-btn" :title="$t('topbar.notifications')" :aria-label="$t('topbar.notifications')">
        <svg class="bell-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" /></svg>
        <span v-if="notifications.items.length" class="notif-count">{{ notifications.items.length }}</span>
      </button>
      <div v-if="auth.isLoggedIn" class="user-chip">
        <div class="user-avatar">{{ (auth.user?.name || 'U').charAt(0) }}</div>
        <div class="user-info">
          <span class="user-name">{{ auth.user?.name || 'User' }}</span>
          <span class="user-org">{{ auth.user?.organization?.name || '' }}</span>
        </div>
      </div>
      <div v-if="!online" class="offline-chip">
        <span class="offline-dot"></span>
        Offline
        <span v-if="pendingCount" class="pending-count">{{ pendingCount }}</span>
      </div>
      <button v-if="auth.isLoggedIn" class="logout-btn" @click="handleLogout">
        {{ $t('auth.logout') }}
      </button>
    </div>
  </header>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useNotificationsStore } from '../../stores/notifications'
import { useOffline } from '../../composables/useOffline'

defineProps({
  showHamburger: { type: Boolean, default: false }
})
defineEmits(['toggle-sidebar'])

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const notifications = useNotificationsStore()
const { online, pendingCount } = useOffline()

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
  padding: 0 20px;
  height: var(--topbar-height);
  min-height: var(--topbar-height);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  gap: 12px;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.hamburger-btn {
  display: none;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.hamburger-btn:hover {
  background: var(--bg);
}

.hamburger-line {
  display: block;
  width: 18px;
  height: 2px;
  background: var(--text);
  border-radius: 1px;
  transition: all 0.2s ease;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.phase-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 10px;
  background: var(--primary);
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  flex-shrink: 0;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.icon-btn {
  position: relative;
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  line-height: 1;
  transition: all 0.15s ease;
}

.icon-btn:hover {
  background: var(--bg);
  border-color: var(--text-secondary);
}

.notif-count {
  position: absolute;
  top: -4px;
  right: -4px;
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

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--primary);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.user-name {
  font-size: 13px;
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
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 13px;
  transition: all 0.15s ease;
}

.logout-btn:hover {
  border-color: var(--danger);
  color: var(--danger);
}

.offline-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: var(--radius);
  background: rgba(231,76,60,0.1);
  color: var(--danger);
  font-size: 12px;
  font-weight: 600;
}

.offline-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--danger);
  animation: pulse-dot 1.5s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.pending-count {
  background: var(--danger);
  color: #fff;
  font-size: 10px;
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

@media (max-width: 767px) {
  .hamburger-btn {
    display: flex;
  }

  .page-title {
    font-size: 16px;
  }

  .user-info {
    display: none;
  }

  .logout-btn {
    display: none;
  }
}

@media (min-width: 768px) and (max-width: 1023px) {
  .user-org {
    display: none;
  }
}
</style>
