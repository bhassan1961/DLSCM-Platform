import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('./views/LoginView.vue'),
    meta: { title: 'Login', phase: 0 }
  },
  {
    path: '/app',
    component: () => import('./components/layout/AppShell.vue'),
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('./views/DashboardView.vue'),
        meta: { title: 'Dashboard', phase: 1 }
      },
      {
        path: 'inventory',
        name: 'Inventory',
        component: () => import('./views/InventoryView.vue'),
        meta: { title: 'Inventory Management', phase: 1 }
      },
      {
        path: 'requests',
        name: 'SupplyRequests',
        component: () => import('./views/SupplyRequestsView.vue'),
        meta: { title: 'Supply Requests', phase: 1 }
      },
      {
        path: 'shipments',
        name: 'Shipments',
        component: () => import('./views/ShipmentsView.vue'),
        meta: { title: 'Shipments', phase: 1 }
      },
      {
        path: 'coordination',
        name: 'Coordination',
        component: () => import('./views/CoordinationView.vue'),
        meta: { title: '3W Coordination', phase: 2 }
      },
      {
        path: 'forecasting',
        name: 'Forecasting',
        component: () => import('./views/ForecastingView.vue'),
        meta: { title: 'Demand Forecasting', phase: 2 }
      },
      {
        path: 'routing',
        name: 'Routing',
        component: () => import('./views/RoutingView.vue'),
        meta: { title: 'Route Optimization', phase: 2 }
      },
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('./views/ReportsView.vue'),
        meta: { title: 'Donor Reports', phase: 2 }
      },
      {
        path: 'marketplace',
        name: 'Marketplace',
        component: () => import('./views/MarketplaceView.vue'),
        meta: { title: 'Surge Marketplace', phase: 3 }
      },
      {
        path: 'simulation',
        name: 'Simulation',
        component: () => import('./views/SimulationView.vue'),
        meta: { title: 'Scenario Simulation', phase: 4 }
      },
      {
        path: 'risk',
        name: 'Risk',
        component: () => import('./views/RiskView.vue'),
        meta: { title: 'Risk Dashboard', phase: 4 }
      },
      {
        path: 'resilience',
        name: 'Resilience',
        component: () => import('./views/ResilienceView.vue'),
        meta: { title: 'Community Toolkit', phase: 4 }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('./views/SettingsView.vue'),
        meta: { title: 'Settings', phase: 0 }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - DLSCM` : 'DLSCM Platform'
})

export default router
