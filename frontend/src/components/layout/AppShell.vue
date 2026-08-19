<template>
  <div class="app-shell" :class="{ 'sidebar-open': sidebarOpen, 'sidebar-collapsed': sidebarCollapsed }">
    <a href="#main-content" class="skip-link">Skip to main content</a>

    <div v-if="sidebarOpen && isMobile" class="sidebar-overlay" @click="sidebarOpen = false"></div>

    <Sidebar
      :collapsed="sidebarCollapsed && !isMobile"
      :class="{ open: sidebarOpen }"
      @nav="sidebarOpen = false"
    />

    <div class="main-area">
      <TopBar @toggle-sidebar="toggleSidebar" :show-hamburger="true" />
      <main id="main-content" class="content" role="main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import Sidebar from './Sidebar.vue'
import TopBar from './TopBar.vue'

const sidebarOpen = ref(false)
const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1280)

const isMobile = computed(() => windowWidth.value < 768)
const isTablet = computed(() => windowWidth.value >= 768 && windowWidth.value < 1024)
const sidebarCollapsed = computed(() => isTablet.value)

function toggleSidebar() {
  if (isMobile.value) {
    sidebarOpen.value = !sidebarOpen.value
  }
}

function onResize() {
  windowWidth.value = window.innerWidth
  if (!isMobile.value) sidebarOpen.value = false
}

onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))
</script>

<style scoped>
.skip-link {
  position: absolute;
  top: -100%;
  left: 16px;
  z-index: 1000;
  padding: 8px 16px;
  background: var(--accent);
  color: #ffffff;
  border-radius: var(--radius-sm);
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
}

.skip-link:focus {
  top: 8px;
}

.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: var(--bg);
}

.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 90;
}

/* Mobile: sidebar hidden by default, slides in as overlay */
@media (max-width: 767px) {
  .content {
    padding: 16px;
  }
}

/* Tablet: sidebar is always visible but collapsed */
@media (min-width: 768px) and (max-width: 1023px) {
  .content {
    padding: 20px;
  }
}
</style>
