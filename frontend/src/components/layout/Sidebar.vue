<template>
  <nav class="sidebar">
    <div class="sidebar-header">
      <div class="logo">DLSCM</div>
      <div class="subtitle">Disaster Logistics Platform</div>
    </div>

    <div class="nav-sections">
      <div class="nav-section">
        <div class="section-label">FOUNDATION</div>
        <router-link to="/app/dashboard" class="nav-item">
          <span class="nav-icon">&#x25A6;</span>
          <span>Dashboard</span>
        </router-link>
        <router-link to="/app/inventory" class="nav-item">
          <span class="nav-icon">&#x25C9;</span>
          <span>Inventory</span>
        </router-link>
        <router-link to="/app/requests" class="nav-item">
          <span class="nav-icon">&#x2197;</span>
          <span>Supply Requests</span>
        </router-link>
        <router-link to="/app/shipments" class="nav-item">
          <span class="nav-icon">&#x25C8;</span>
          <span>Shipments</span>
        </router-link>
      </div>

      <div class="nav-section">
        <div class="section-label">INTELLIGENCE</div>
        <router-link to="/app/coordination" class="nav-item">
          <span class="nav-icon">&#x25CE;</span>
          <span>3W Coordination</span>
        </router-link>
        <router-link to="/app/forecasting" class="nav-item">
          <span class="nav-icon">&#x229E;</span>
          <span>Demand Forecast</span>
        </router-link>
        <router-link to="/app/routing" class="nav-item">
          <span class="nav-icon">&#x25BF;</span>
          <span>Route Optimizer</span>
        </router-link>
        <router-link to="/app/reports" class="nav-item">
          <span class="nav-icon">&#x25EB;</span>
          <span>Donor Reports</span>
        </router-link>
      </div>

      <div class="nav-section">
        <div class="section-label">SCALE</div>
        <router-link to="/app/marketplace" class="nav-item">
          <span class="nav-icon">&#x2295;</span>
          <span>Surge Marketplace</span>
        </router-link>
      </div>

      <div class="nav-section">
        <div class="section-label">ECOSYSTEM</div>
        <router-link to="/app/simulation" class="nav-item">
          <span class="nav-icon">&#x25A3;</span>
          <span>Simulation</span>
        </router-link>
        <router-link to="/app/risk" class="nav-item">
          <span class="nav-icon">&#x2298;</span>
          <span>Risk Dashboard</span>
        </router-link>
        <router-link to="/app/resilience" class="nav-item">
          <span class="nav-icon">&#x229B;</span>
          <span>Community Toolkit</span>
        </router-link>
      </div>
    </div>

    <div class="sidebar-footer">
      <router-link to="/app/settings" class="nav-item">
        <span class="nav-icon">&#x2699;</span>
        <span>Settings</span>
      </router-link>
    </div>
  </nav>
</template>

<style scoped>
.sidebar {
  width: 260px;
  min-width: 260px;
  background: var(--primary);
  color: #ffffff;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow-y: auto;
}

.sidebar-header {
  padding: 24px 20px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 2px;
}

.subtitle {
  font-size: 11px;
  opacity: 0.6;
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.nav-sections {
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
}

.nav-section {
  margin-bottom: 8px;
}

.section-label {
  padding: 12px 20px 6px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1.5px;
  opacity: 0.4;
  text-transform: uppercase;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  color: rgba(255, 255, 255, 0.75);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.15s ease;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.nav-item.router-link-active {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
  border-left-color: var(--accent);
}

.nav-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
}

.sidebar-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 8px 0;
}
</style>
