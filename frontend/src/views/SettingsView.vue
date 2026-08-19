<template>
  <div class="settings">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <div class="page-header">
      <h2>{{ $t('settings.title') }}</h2>
      <p class="page-subtitle">{{ $t('settings.subtitle') }}</p>
    </div>

    <div class="settings-sections">
      <!-- Profile -->
      <div class="settings-card">
        <h3 class="card-title">{{ $t('settings.profile') }}</h3>
        <div class="profile-fields">
          <div class="field-row">
            <span class="field-label">{{ $t('settings.name') }}</span>
            <span class="field-value">{{ user?.name || user?.full_name || $t('settings.notSet') }}</span>
          </div>
          <div class="field-row">
            <span class="field-label">{{ $t('settings.email') }}</span>
            <span class="field-value">{{ user?.email || $t('settings.notSet') }}</span>
          </div>
          <div class="field-row">
            <span class="field-label">{{ $t('settings.role') }}</span>
            <span class="field-value">
              <span class="role-badge">{{ user?.role || 'User' }}</span>
            </span>
          </div>
          <div class="field-row">
            <span class="field-label">{{ $t('settings.organization') }}</span>
            <span class="field-value">{{ user?.organization?.name || user?.org_name || $t('settings.notAssigned') }}</span>
          </div>
        </div>
      </div>

      <!-- Preferences -->
      <div class="settings-card">
        <h3 class="card-title">{{ $t('settings.preferences') }}</h3>
        <div class="pref-list">
          <div class="pref-row">
            <div class="pref-info">
              <span class="pref-label">{{ $t('settings.notifications') }}</span>
              <span class="pref-desc">{{ $t('settings.notificationsDesc') }}</span>
            </div>
            <button
              class="toggle-btn"
              :class="{ active: prefs.notifications }"
              @click="prefs.notifications = !prefs.notifications"
            >
              <span class="toggle-knob"></span>
            </button>
          </div>
          <div class="pref-row">
            <div class="pref-info">
              <span class="pref-label">{{ $t('settings.darkMode') }}</span>
              <span class="pref-desc">{{ $t('settings.darkModeDesc') }}</span>
            </div>
            <button
              class="toggle-btn"
              :class="{ active: prefs.darkMode }"
              @click="prefs.darkMode = !prefs.darkMode"
            >
              <span class="toggle-knob"></span>
            </button>
          </div>
          <div class="pref-row">
            <div class="pref-info">
              <span class="pref-label">{{ $t('settings.language') }}</span>
              <span class="pref-desc">{{ $t('settings.languageDesc') }}</span>
            </div>
            <select v-model="prefs.language" class="lang-select" @change="changeLanguage">
              <option value="en">English</option>
              <option value="fr">Fran&#231;ais</option>
              <option value="es">Espa&#241;ol</option>
              <option value="ar">&#1575;&#1604;&#1593;&#1585;&#1576;&#1610;&#1577;</option>
              <option value="zh">&#20013;&#25991;</option>
              <option value="ru">&#1056;&#1091;&#1089;&#1089;&#1082;&#1080;&#1081;</option>
            </select>
          </div>
        </div>
      </div>

      <!-- About -->
      <div class="settings-card">
        <h3 class="card-title">{{ $t('settings.about') }}</h3>
        <div class="about-content">
          <div class="field-row">
            <span class="field-label">{{ $t('settings.platformVersion') }}</span>
            <span class="field-value version-tag">0.1.0</span>
          </div>
          <p class="about-text">{{ $t('settings.aboutText') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import { setLocale } from '../i18n'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const { locale } = useI18n()
const authStore = useAuthStore()
const user = computed(() => authStore.user)

const prefs = reactive({
  notifications: true,
  darkMode: true,
  language: locale.value
})

function changeLanguage() {
  setLocale(prefs.language)
}

function retryLoad() {
  window.location.reload()
}
</script>

<style scoped>
.settings {
  max-width: 700px;
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

.settings-sections {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

/* Profile fields */
.profile-fields {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.field-label {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.field-value {
  font-size: 14px;
  color: var(--text);
  font-weight: 500;
}

.role-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--radius);
  background: rgba(30, 58, 95, 0.12);
  color: var(--primary);
  text-transform: capitalize;
}

.version-tag {
  font-family: monospace;
  font-size: 13px;
  padding: 3px 10px;
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--accent);
}

/* Preferences */
.pref-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pref-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}

.pref-row:last-child {
  border-bottom: none;
}

.pref-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pref-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
}

.pref-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

/* Toggle button */
.toggle-btn {
  position: relative;
  width: 44px;
  height: 24px;
  border: none;
  border-radius: var(--radius);
  background: var(--border);
  cursor: pointer;
  transition: background 0.2s ease;
  padding: 0;
  flex-shrink: 0;
}

.toggle-btn.active {
  background: var(--success);
}

.toggle-knob {
  position: absolute;
  top: 2px;
  inset-inline-start: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ffffff;
  transition: transform 0.2s ease;
  box-shadow: var(--shadow);
}

.toggle-btn.active .toggle-knob {
  transform: translateX(20px);
}

:root[dir="rtl"] .toggle-btn.active .toggle-knob {
  transform: translateX(-20px);
}

.lang-select {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text);
  font-size: 13px;
  cursor: pointer;
}

.lang-select:focus {
  outline: none;
  border-color: var(--primary);
}

/* About */
.about-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.about-text {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
}
</style>
