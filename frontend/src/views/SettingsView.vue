<template>
  <div class="settings">
    <div class="page-header">
      <h2>Settings</h2>
      <p class="page-subtitle">Platform configuration and user preferences</p>
    </div>

    <div class="settings-sections">
      <!-- Profile -->
      <div class="settings-card">
        <h3 class="card-title">Profile</h3>
        <div class="profile-fields">
          <div class="field-row">
            <span class="field-label">Name</span>
            <span class="field-value">{{ user?.name || user?.full_name || 'Not set' }}</span>
          </div>
          <div class="field-row">
            <span class="field-label">Email</span>
            <span class="field-value">{{ user?.email || 'Not set' }}</span>
          </div>
          <div class="field-row">
            <span class="field-label">Role</span>
            <span class="field-value">
              <span class="role-badge">{{ user?.role || 'User' }}</span>
            </span>
          </div>
          <div class="field-row">
            <span class="field-label">Organization</span>
            <span class="field-value">{{ user?.organization?.name || user?.org_name || 'Not assigned' }}</span>
          </div>
        </div>
      </div>

      <!-- Preferences -->
      <div class="settings-card">
        <h3 class="card-title">Preferences</h3>
        <div class="pref-list">
          <div class="pref-row">
            <div class="pref-info">
              <span class="pref-label">Notifications</span>
              <span class="pref-desc">Receive alerts for disasters and supply requests</span>
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
              <span class="pref-label">Dark Mode</span>
              <span class="pref-desc">Use dark theme for the platform interface</span>
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
              <span class="pref-label">Language</span>
              <span class="pref-desc">Display language for the platform</span>
            </div>
            <select v-model="prefs.language" class="lang-select">
              <option value="en">English</option>
              <option value="fr">French</option>
              <option value="es">Spanish</option>
              <option value="ar">Arabic</option>
            </select>
          </div>
        </div>
      </div>

      <!-- About -->
      <div class="settings-card">
        <h3 class="card-title">About</h3>
        <div class="about-content">
          <div class="field-row">
            <span class="field-label">Platform Version</span>
            <span class="field-value version-tag">0.1.0</span>
          </div>
          <p class="about-text">
            The Disaster Logistics &amp; Supply Chain Management (DLSCM) platform
            provides end-to-end coordination for humanitarian supply chains. It supports
            real-time inventory tracking, demand forecasting, multi-organization
            coordination, risk assessment, and scenario simulation to improve disaster
            preparedness and response efficiency.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const user = computed(() => authStore.user)

const prefs = reactive({
  notifications: true,
  darkMode: true,
  language: 'en'
})
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
  border-radius: 8px;
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
  border-radius: 10px;
  background: rgba(30, 58, 95, 0.12);
  color: var(--primary);
  text-transform: capitalize;
}

.version-tag {
  font-family: monospace;
  font-size: 13px;
  padding: 3px 10px;
  border-radius: 6px;
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
  border-radius: 12px;
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
  left: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ffffff;
  transition: transform 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.toggle-btn.active .toggle-knob {
  transform: translateX(20px);
}

.lang-select {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
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
