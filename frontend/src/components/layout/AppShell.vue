<template>
  <div class="app-shell">
    <Sidebar />
    <div class="main-area">
      <TopBar />
      <div class="content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import TopBar from './TopBar.vue'
</script>

<style scoped>
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
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: var(--bg);
}
</style>
