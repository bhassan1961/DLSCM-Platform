import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

export const authApi = {
  login: (email) => api.post('/auth/login', { email }),
  listUsers: () => api.get('/auth/users')
}

export const dashboardApi = {
  stats: () => api.get('/dashboard/stats')
}

export const inventoryApi = {
  warehouses: () => api.get('/inventory/warehouses'),
  warehouseStock: (id) => api.get(`/inventory/warehouses/${id}/stock`),
  allStock: (category) => api.get('/inventory/stock', { params: { category } }),
  items: () => api.get('/inventory/items'),
  updateStock: (id, quantity) => api.patch(`/inventory/stock/${id}`, { quantity })
}

export const requestsApi = {
  list: (status) => api.get('/requests', { params: { status } }),
  create: (data) => api.post('/requests', data),
  updateStatus: (id, status) => api.patch(`/requests/${id}/status`, { status })
}

export const disastersApi = {
  list: (status) => api.get('/disasters', { params: { status } }),
  get: (id) => api.get(`/disasters/${id}`)
}

export const alertsApi = {
  list: (severity) => api.get('/alerts', { params: { severity } }),
  acknowledge: (id) => api.post(`/alerts/${id}/acknowledge`)
}

export const shipmentsApi = {
  list: () => api.get('/shipments')
}

export const coordinationApi = {
  list: () => api.get('/coordination')
}

export const forecastApi = {
  forecast: (disasterId, days) => api.get(`/forecasting/${disasterId}`, { params: { days } })
}

export const routingApi = {
  optimize: (data) => api.post('/routing/optimize', data)
}

export const reportsApi = {
  generate: (data) => api.post('/reports/generate', data)
}

export const sitrepApi = {
  parse: (text) => api.post('/sitrep/parse', { text })
}

export const marketplaceApi = {
  list: () => api.get('/marketplace')
}

export const simulationApi = {
  run: (data) => api.post('/simulation/run', data),
  scenarios: () => api.get('/simulation/scenarios')
}

export const riskApi = {
  map: () => api.get('/risk/map')
}

export default api
