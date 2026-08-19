import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('dlscm_access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auto-refresh on 401
let refreshPromise = null
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refreshToken = localStorage.getItem('dlscm_refresh_token')
      if (!refreshToken) return Promise.reject(error)

      if (!refreshPromise) {
        refreshPromise = api.post('/auth/refresh', { refresh_token: refreshToken })
          .then(({ data }) => {
            localStorage.setItem('dlscm_access_token', data.access_token)
            localStorage.setItem('dlscm_refresh_token', data.refresh_token)
            localStorage.setItem('dlscm_user', JSON.stringify(data.user))
            refreshPromise = null
            return data.access_token
          })
          .catch((e) => {
            refreshPromise = null
            localStorage.removeItem('dlscm_access_token')
            localStorage.removeItem('dlscm_refresh_token')
            localStorage.removeItem('dlscm_user')
            window.location.href = '/login'
            return Promise.reject(e)
          })
      }

      const newToken = await refreshPromise
      original.headers.Authorization = `Bearer ${newToken}`
      return api(original)
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  refresh: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),
  me: () => api.get('/auth/me'),
  changePassword: (data) => api.post('/auth/change-password', data),
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
  createItem: (data) => api.post('/inventory/items', data),
  deleteItem: (id) => api.delete(`/inventory/items/${id}`),
  updateStock: (id, quantity) => api.patch(`/inventory/stock/${id}`, { quantity }),
  crossOrg: () => api.get('/inventory/cross-org')
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
  acknowledge: (id) => api.patch(`/alerts/${id}/acknowledge`)
}

export const shipmentsApi = {
  list: () => api.get('/shipments'),
  create: (data) => api.post('/shipments', data),
  updateStatus: (id, status) => api.patch(`/shipments/${id}/status`, { status }),
  delete: (id) => api.delete(`/shipments/${id}`)
}

export const coordinationApi = {
  list: () => api.get('/coordination'),
  create: (data) => api.post('/coordination', data),
  update: (id, data) => api.patch(`/coordination/${id}`, data),
  delete: (id) => api.delete(`/coordination/${id}`)
}

export const forecastApi = {
  forecast: (disasterId, days) => api.get(`/forecasting/${disasterId}`, { params: { days } })
}

export const routingApi = {
  optimize: (data) => api.post('/routing/optimize', data),
  conditions: () => api.get('/routing/conditions'),
}

export const reportsApi = {
  list: () => api.get('/reports'),
  generate: (data) => api.post('/reports/generate', data)
}

export const sitrepApi = {
  parse: (text) => api.post('/sitrep/parse', { text })
}

export const marketplaceApi = {
  list: () => api.get('/marketplace'),
  match: (listingId) => api.post(`/marketplace/${listingId}/match`),
  book: (listingId, data) => api.post(`/marketplace/${listingId}/book`, data),
  cancelBooking: (bookingId) => api.patch(`/marketplace/bookings/${bookingId}/cancel`),
  bookings: () => api.get('/marketplace/bookings'),
}

export const simulationApi = {
  run: (data) => api.post('/simulation/run', data),
  scenarios: () => api.get('/simulation/scenarios')
}

export const riskApi = {
  map: () => api.get('/risk/map')
}

export const suppliersApi = {
  list: (category) => api.get('/suppliers', { params: { category } }),
  create: (data) => api.post('/suppliers', data),
  update: (id, data) => api.patch(`/suppliers/${id}`, data)
}

export const kitsApi = {
  list: () => api.get('/kits'),
  create: (data) => api.post('/kits', data)
}

export const auditApi = {
  list: (resource_type) => api.get('/audit', { params: { resource_type } })
}

export const donationsApi = {
  list: (status) => api.get('/donations', { params: { status } }),
  create: (data) => api.post('/donations', data),
  updateStatus: (id, status) => api.patch(`/donations/${id}/status`, { status })
}

export const complianceApi = {
  check: () => api.get('/compliance')
}

export const afterActionApi = {
  list: (disasterId) => api.get(`/reports/after-action/${disasterId}`),
  create: (data) => api.post('/reports/after-action', data)
}

export const intelligenceApi = {
  list: () => api.get('/intelligence'),
  get: (disasterId, params) => api.get(`/intelligence/${disasterId}`, { params }),
  liveAlerts: () => api.get('/intelligence/live-alerts'),
  newsFeeds: () => api.get('/intelligence/news-feeds'),
  liveNews: (feeds, limit) => api.get('/intelligence/news', { params: { feeds, limit } })
}

export const prepositioningApi = {
  recommendations: () => api.get('/prepositioning/recommendations'),
}

export const edxlApi = {
  wrapAlert: (alertId) => api.post(`/edxl/wrap-alert/${alertId}`),
  wrapSitrep: (data) => api.post('/edxl/wrap-sitrep', data),
  parse: (xml) => api.post('/edxl/parse', xml, { headers: { 'Content-Type': 'text/xml' } }),
  capGenerate: (data) => api.post('/edxl/cap/generate', data),
}

export const recoveryApi = {
  plans: (disasterId) => api.get(`/recovery/plans`, { params: { disaster_id: disasterId } }),
  createPlan: (data) => api.post('/recovery/plans', data),
  updatePhase: (planId, data) => api.patch(`/recovery/plans/${planId}/phase`, data),
  procurement: (planId) => api.get(`/recovery/plans/${planId}/procurement`),
  addProcurement: (planId, data) => api.post(`/recovery/plans/${planId}/procurement`, data),
}

export default api
