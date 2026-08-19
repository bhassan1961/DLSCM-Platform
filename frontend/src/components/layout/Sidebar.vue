<template>
  <nav class="sidebar" :class="{ collapsed }" aria-label="Main navigation">
    <div class="sidebar-header">
      <div class="logo-area">
        <div class="logo-mark">D</div>
        <transition name="fade">
          <div v-if="!collapsed" class="logo-text">
            <div class="logo">DLSCM</div>
            <div class="subtitle">Disaster Logistics</div>
          </div>
        </transition>
      </div>
    </div>

    <div class="nav-sections">
      <div class="nav-section">
        <div class="section-label">{{ collapsed ? '' : $t('nav.foundation').toUpperCase() }}</div>
        <router-link to="/app/dashboard" class="nav-item" :title="collapsed ? $t('nav.dashboard') : undefined" @click="$emit('nav')">
          <SvgIcon name="dashboard" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.dashboard') }}</span>
        </router-link>
        <router-link to="/app/inventory" class="nav-item" :title="collapsed ? $t('nav.inventory') : undefined" @click="$emit('nav')">
          <SvgIcon name="inventory" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.inventory') }}</span>
        </router-link>
        <router-link to="/app/requests" class="nav-item" :title="collapsed ? $t('nav.requests') : undefined" @click="$emit('nav')">
          <SvgIcon name="requests" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.requests') }}</span>
        </router-link>
        <router-link to="/app/shipments" class="nav-item" :title="collapsed ? $t('nav.shipments') : undefined" @click="$emit('nav')">
          <SvgIcon name="shipments" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.shipments') }}</span>
        </router-link>
        <router-link to="/app/suppliers" class="nav-item" :title="collapsed ? $t('nav.suppliers') : undefined" @click="$emit('nav')">
          <SvgIcon name="suppliers" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.suppliers') }}</span>
        </router-link>
        <router-link to="/app/kits" class="nav-item" :title="collapsed ? $t('nav.kits') : undefined" @click="$emit('nav')">
          <SvgIcon name="kits" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.kits') }}</span>
        </router-link>
        <router-link to="/app/donations" class="nav-item" :title="collapsed ? $t('nav.donations') : undefined" @click="$emit('nav')">
          <SvgIcon name="donations" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.donations') }}</span>
        </router-link>
        <router-link to="/app/cross-org" class="nav-item" :title="collapsed ? $t('nav.crossOrg') : undefined" @click="$emit('nav')">
          <SvgIcon name="cross-org" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.crossOrg') }}</span>
        </router-link>
        <router-link to="/app/prepositioning" class="nav-item" :title="collapsed ? $t('nav.prepositioning') : undefined" @click="$emit('nav')">
          <SvgIcon name="inventory" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.prepositioning') }}</span>
        </router-link>
      </div>

      <div class="nav-section">
        <div class="section-label">{{ collapsed ? '' : $t('nav.intelligence').toUpperCase() }}</div>
        <router-link to="/app/intelligence" class="nav-item" :title="collapsed ? $t('nav.crisisIntel') : undefined" @click="$emit('nav')">
          <SvgIcon name="intelligence" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.crisisIntel') }}</span>
        </router-link>
        <router-link to="/app/coordination" class="nav-item" :title="collapsed ? $t('nav.coordination') : undefined" @click="$emit('nav')">
          <SvgIcon name="coordination" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.coordination') }}</span>
        </router-link>
        <router-link to="/app/forecasting" class="nav-item" :title="collapsed ? $t('nav.forecasting') : undefined" @click="$emit('nav')">
          <SvgIcon name="forecast" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.forecasting') }}</span>
        </router-link>
        <router-link to="/app/routing" class="nav-item" :title="collapsed ? $t('nav.routing') : undefined" @click="$emit('nav')">
          <SvgIcon name="routing" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.routing') }}</span>
        </router-link>
        <router-link to="/app/reports" class="nav-item" :title="collapsed ? $t('nav.reports') : undefined" @click="$emit('nav')">
          <SvgIcon name="reports" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.reports') }}</span>
        </router-link>
        <router-link to="/app/compliance" class="nav-item" :title="collapsed ? $t('nav.compliance') : undefined" @click="$emit('nav')">
          <SvgIcon name="compliance" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.compliance') }}</span>
        </router-link>
        <router-link to="/app/edxl" class="nav-item" :title="collapsed ? $t('nav.edxl') : undefined" @click="$emit('nav')">
          <SvgIcon name="coordination" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.edxl') }}</span>
        </router-link>
      </div>

      <div class="nav-section">
        <div class="section-label">{{ collapsed ? '' : $t('nav.scale').toUpperCase() }}</div>
        <router-link to="/app/marketplace" class="nav-item" :title="collapsed ? $t('nav.marketplace') : undefined" @click="$emit('nav')">
          <SvgIcon name="marketplace" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.marketplace') }}</span>
        </router-link>
        <router-link to="/app/after-action" class="nav-item" :title="collapsed ? $t('nav.afterAction') : undefined" @click="$emit('nav')">
          <SvgIcon name="after-action" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.afterAction') }}</span>
        </router-link>
        <router-link to="/app/recovery" class="nav-item" :title="collapsed ? $t('nav.recovery') : undefined" @click="$emit('nav')">
          <SvgIcon name="reports" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.recovery') }}</span>
        </router-link>
      </div>

      <div class="nav-section">
        <div class="section-label">{{ collapsed ? '' : $t('nav.ecosystem').toUpperCase() }}</div>
        <router-link to="/app/simulation" class="nav-item" :title="collapsed ? $t('nav.simulation') : undefined" @click="$emit('nav')">
          <SvgIcon name="simulation" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.simulation') }}</span>
        </router-link>
        <router-link to="/app/risk" class="nav-item" :title="collapsed ? $t('nav.risk') : undefined" @click="$emit('nav')">
          <SvgIcon name="risk" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.risk') }}</span>
        </router-link>
        <router-link to="/app/resilience" class="nav-item" :title="collapsed ? $t('nav.resilience') : undefined" @click="$emit('nav')">
          <SvgIcon name="resilience" :size="18" />
          <span v-if="!collapsed" class="nav-text">{{ $t('nav.resilience') }}</span>
        </router-link>
      </div>
    </div>

    <div class="sidebar-footer">
      <router-link to="/app/audit" class="nav-item" :title="collapsed ? $t('nav.audit') : undefined" @click="$emit('nav')">
        <SvgIcon name="audit" :size="18" />
        <span v-if="!collapsed" class="nav-text">{{ $t('nav.audit') }}</span>
      </router-link>
      <router-link to="/app/settings" class="nav-item" :title="collapsed ? $t('nav.settings') : undefined" @click="$emit('nav')">
        <SvgIcon name="settings" :size="18" />
        <span v-if="!collapsed" class="nav-text">{{ $t('nav.settings') }}</span>
      </router-link>
    </div>
  </nav>
</template>

<script setup>
import SvgIcon from '../common/SvgIcon.vue'

defineProps({
  collapsed: { type: Boolean, default: false }
})
defineEmits(['nav'])
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: linear-gradient(180deg, #162a45 0%, #0f1f35 100%);
  color: #ffffff;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  transition: width 0.25s ease, min-width 0.25s ease, transform 0.25s ease;
  z-index: 100;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed);
  min-width: var(--sidebar-collapsed);
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-mark {
  width: 36px;
  height: 36px;
  background: var(--accent);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0;
  flex-shrink: 0;
}

.logo-text {
  overflow: hidden;
  white-space: nowrap;
}

.logo {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 1.5px;
  line-height: 1.2;
}

.subtitle {
  font-size: 10px;
  opacity: 0.5;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.nav-sections {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;
}

.nav-section {
  margin-bottom: 4px;
}

.section-label {
  padding: 14px 20px 6px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1.5px;
  opacity: 0.35;
  text-transform: uppercase;
  min-height: 20px;
}

.collapsed .section-label {
  padding: 10px 0 4px;
  text-align: center;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 20px;
  color: rgba(255, 255, 255, 0.65);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s ease;
  border-inline-start: 3px solid transparent;
  white-space: nowrap;
}

.collapsed .nav-item {
  padding: 10px 0;
  justify-content: center;
  border-inline-start: none;
  border-inline-end: 3px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #ffffff;
}

.nav-item.router-link-active {
  background: rgba(232, 145, 58, 0.12);
  color: #ffffff;
  border-inline-start-color: var(--accent);
}

.collapsed .nav-item.router-link-active {
  border-inline-start-color: transparent;
  border-inline-end-color: var(--accent);
}

.nav-item :deep(.svg-icon) {
  opacity: 0.85;
  flex-shrink: 0;
}

.nav-item.router-link-active :deep(.svg-icon) {
  opacity: 1;
}

.nav-text {
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding: 8px 0;
}

/* Mobile: sidebar is off-screen, slides in with .open */
@media (max-width: 767px) {
  .sidebar {
    position: fixed;
    inset-inline-start: 0;
    top: 0;
    transform: translateX(-100%);
    width: var(--sidebar-width) !important;
    min-width: var(--sidebar-width) !important;
    box-shadow: var(--shadow-lg);
  }

  :root[dir="rtl"] .sidebar {
    transform: translateX(100%);
  }

  .sidebar.open {
    transform: translateX(0);
  }
}
</style>
