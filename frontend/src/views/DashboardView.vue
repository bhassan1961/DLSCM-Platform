<template>
  <div class="dashboard">
    <ErrorBanner :error="error" :on-retry="retryLoad" @dismiss="clearError" />
    <!-- News Ticker -->
    <div class="ticker-panel">
      <div class="ticker-header">
        <div class="ticker-label">
          <span class="ticker-live-dot"></span>
          <span class="ticker-title">Live News</span>
        </div>
        <div class="ticker-controls">
          <button
            v-for="feed in tickerFeeds"
            :key="feed.id"
            class="feed-toggle"
            :class="{ active: activeFeedIds.includes(feed.id) }"
            @click="toggleFeed(feed.id)"
            :title="feed.name"
          >{{ feed.name }}</button>
          <button class="ticker-pause" @click="tickerPaused = !tickerPaused" :title="tickerPaused ? 'Resume' : 'Pause'">
            {{ tickerPaused ? '▶' : '❚❚' }}
          </button>
          <span class="ticker-separator"></span>
          <button class="live-tv-btn" @click="showLiveTV = true" :title="$t('dashboard.liveTv')">
            <SvgIcon name="tv" :size="14" />
            <span>{{ $t('dashboard.liveTv') }}</span>
          </button>
        </div>
      </div>
      <div class="ticker-track-wrapper">
        <div v-if="newsLoading" class="ticker-loading">{{ $t('common.loading') }}</div>
        <div v-else-if="!newsItems.length" class="ticker-loading">{{ $t('common.noData') }}</div>
        <div v-else class="ticker-track" :class="{ paused: tickerPaused }" :style="{ animationDuration: tickerDuration + 's' }">
          <a
            v-for="item in tickerItems"
            :key="item.id"
            class="ticker-item"
            :href="item.url"
            target="_blank"
            rel="noopener"
            @mouseenter="tickerPaused = true"
            @mouseleave="tickerPaused = false"
          >
            <span class="ticker-feed-badge" :class="'feed-' + item.feed_id">{{ item.feed_name }}</span>
            <span class="ticker-headline">{{ item.title }}</span>
            <span v-if="item.published_at" class="ticker-time">{{ tickerTime(item.published_at) }}</span>
          </a>
        </div>
      </div>
    </div>

    <!-- Stat Cards Row -->
    <div class="stats-row">
      <StatCard
        :label="$t('dashboard.activeDisasters')"
        :value="stats.active_disasters ?? '-'"
        icon-name="alert"
        color="var(--danger)"
        clickable
        :active="activePanel === 'disasters'"
        @select="togglePanel('disasters')"
      />
      <StatCard
        :label="$t('dashboard.pendingRequests')"
        :value="stats.pending_requests ?? '-'"
        icon-name="mail"
        color="var(--warning)"
        clickable
        :active="activePanel === 'requests'"
        @select="togglePanel('requests')"
      />
      <StatCard
        :label="$t('dashboard.inTransitShipments')"
        :value="stats.in_transit_shipments ?? '-'"
        icon-name="truck"
        color="var(--accent)"
        clickable
        :active="activePanel === 'shipments'"
        @select="togglePanel('shipments')"
      />
      <StatCard
        :label="$t('dashboard.activeAlerts')"
        :value="stats.active_alerts ?? '-'"
        icon-name="bell"
        color="var(--primary)"
        clickable
        :active="activePanel === 'alerts'"
        @select="togglePanel('alerts')"
      />
    </div>

    <!-- Detail Panel -->
    <transition name="slide">
      <div v-if="activePanel" class="detail-panel">
        <div class="detail-header">
          <h3 class="detail-title">{{ panelTitle }}</h3>
          <button class="detail-close" @click="activePanel = null" aria-label="Close">&times;</button>
        </div>

        <div v-if="panelLoading" class="detail-loading">
          <div class="spinner"></div>
        </div>

        <!-- Active Disasters -->
        <div v-else-if="activePanel === 'disasters'" class="detail-body">
          <div v-if="!detailDisasters.length" class="detail-empty">{{ $t('dashboard.noAlerts') }}</div>
          <div v-for="d in detailDisasters" :key="d.id" class="detail-row disaster-row">
            <div class="row-main">
              <div class="row-title">{{ d.name }}</div>
              <div class="row-meta">
                <span class="meta-item">{{ d.country }}{{ d.region ? ' — ' + d.region : '' }}</span>
                <span class="meta-item type-label">{{ d.disaster_type }}</span>
              </div>
            </div>
            <div class="row-stats">
              <StatusBadge :status="d.severity" size="sm" />
              <span class="pop-stat">{{ formatPop(d.affected_population) }} affected</span>
            </div>
          </div>
        </div>

        <!-- Pending Requests -->
        <div v-else-if="activePanel === 'requests'" class="detail-body">
          <div v-if="!detailRequests.length" class="detail-empty">{{ $t('common.noData') }}</div>
          <div v-for="r in detailRequests" :key="r.id" class="detail-row">
            <div class="row-main">
              <div class="row-title">{{ r.title || r.item_name || 'Request #' + r.id }}</div>
              <div class="row-meta">
                <span class="meta-item">{{ r.disaster_name || 'General' }}</span>
                <span v-if="r.destination" class="meta-item">To: {{ r.destination }}</span>
                <span v-if="r.quantity" class="meta-item">Qty: {{ r.quantity }}</span>
              </div>
            </div>
            <div class="row-stats">
              <StatusBadge :status="r.priority || 'pending'" size="sm" />
              <span v-if="r.created_at" class="time-stat">{{ formatTime(r.created_at) }}</span>
            </div>
          </div>
        </div>

        <!-- In-Transit Shipments -->
        <div v-else-if="activePanel === 'shipments'" class="detail-body">
          <div v-if="!detailShipments.length" class="detail-empty">{{ $t('common.noData') }}</div>
          <div v-for="s in detailShipments" :key="s.id" class="detail-row">
            <div class="row-main">
              <div class="row-title">{{ s.tracking_id }}</div>
              <div class="row-meta">
                <span v-if="s.carrier" class="meta-item">{{ s.carrier }}</span>
                <span class="meta-item type-label">{{ s.transport_mode }}</span>
                <span v-if="s.notes" class="meta-item">{{ s.notes }}</span>
              </div>
            </div>
            <div class="row-stats">
              <StatusBadge :status="s.status" size="sm" />
              <span v-if="s.eta" class="time-stat">ETA: {{ formatDate(s.eta) }}</span>
            </div>
          </div>
        </div>

        <!-- Active Alerts -->
        <div v-else-if="activePanel === 'alerts'" class="detail-body">
          <div v-if="!detailAlerts.length" class="detail-empty">{{ $t('dashboard.noAlerts') }}</div>
          <div v-for="a in detailAlerts" :key="a.id" class="detail-row alert-row">
            <div class="row-main">
              <div class="row-title">{{ a.title }}</div>
              <div class="row-desc">{{ a.description }}</div>
              <div class="row-meta">
                <span v-if="a.disaster_name" class="meta-item">{{ a.disaster_name }}</span>
                <span v-if="a.created_at" class="meta-item">{{ formatTime(a.created_at) }}</span>
              </div>
            </div>
            <div class="row-stats">
              <StatusBadge :status="a.severity" size="sm" />
              <button
                v-if="!a.acknowledged"
                class="ack-btn-sm"
                @click.stop="acknowledgeAlert(a.id)"
              >Ack</button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Crisis Alert Banner -->
    <transition name="slide">
      <div v-if="crisisAlert" class="crisis-alert-banner" @click="focusCrisis(crisisAlert)">
        <div class="crisis-alert-icon">
          <SvgIcon name="alert" :size="20" />
        </div>
        <div class="crisis-alert-body">
          <span class="crisis-alert-label">{{ $t('dashboard.activeAlerts') }}</span>
          <span class="crisis-alert-title">{{ crisisAlert.title }}</span>
          <span v-if="crisisAlert.country" class="crisis-alert-location">{{ crisisAlert.country }}</span>
        </div>
        <button class="crisis-alert-focus">{{ $t('common.viewAll') }}</button>
        <button class="crisis-alert-dismiss" @click.stop="dismissCrisisAlert" aria-label="Dismiss">&times;</button>
      </div>
    </transition>

    <!-- Main Content -->
    <div class="dashboard-main">
      <!-- Map -->
      <div class="map-panel">
        <div class="panel-header">
          <h2 class="panel-title">{{ $t('dashboard.globalMap') }}</h2>
          <button class="map-filter-toggle" @click="showMapFilters = !showMapFilters">
            <SvgIcon name="filter" :size="14" />
            <span>{{ $t('dashboard.filters') }}</span>
            <span v-if="activeFilterCount" class="filter-count">{{ activeFilterCount }}</span>
          </button>
        </div>
        <transition name="slide">
          <div v-if="showMapFilters" class="map-filters">
            <div class="filter-group">
              <span class="filter-group-label">{{ $t('common.filter') }}</span>
              <button
                v-for="layer in mapLayers"
                :key="layer.id"
                class="map-filter-btn"
                :class="{ active: mapLayerFlags[layer.id] }"
                @click="mapLayerFlags[layer.id] = !mapLayerFlags[layer.id]"
              >
                <span class="filter-dot" :style="{ background: layer.color }"></span>
                {{ layer.label }}
              </button>
            </div>
            <div class="filter-group">
              <span class="filter-group-label">{{ $t('risk.riskLevel') }}</span>
              <button
                v-for="level in alertLevels"
                :key="level.id"
                class="map-filter-btn"
                :class="{ active: mapAlertLevelFlags[level.id] }"
                @click="mapAlertLevelFlags[level.id] = !mapAlertLevelFlags[level.id]"
              >
                <span class="filter-dot" :style="{ background: level.color }"></span>
                {{ level.label }}
              </button>
            </div>
            <div class="filter-group">
              <span class="filter-group-label">{{ $t('common.type') }}</span>
              <button
                v-for="etype in eventTypes"
                :key="etype.id"
                class="map-filter-btn"
                :class="{ active: mapEventTypeFlags[etype.id] }"
                @click="mapEventTypeFlags[etype.id] = !mapEventTypeFlags[etype.id]"
              >
                <span class="filter-icon">{{ etype.icon }}</span>
                {{ etype.label }}
              </button>
            </div>
          </div>
        </transition>
        <div class="map-wrapper">
          <MapView
            :markers="mapMarkers"
            :center="mapCenter"
            :zoom="mapZoom"
          />
        </div>
      </div>

      <!-- Live TV Modal -->
      <teleport to="body">
        <transition name="fade">
          <div v-if="showLiveTV" class="livetv-overlay" @click.self="showLiveTV = false">
            <div class="livetv-modal">
              <div class="livetv-header">
                <div class="livetv-title-row">
                  <span class="livetv-dot"></span>
                  <h2 class="livetv-heading">{{ $t('dashboard.liveTv') }}</h2>
                </div>
                <button class="livetv-close" @click="showLiveTV = false" aria-label="Close">&times;</button>
              </div>
              <div class="livetv-channels">
                <button
                  v-for="ch in liveChannels"
                  :key="ch.id"
                  class="channel-btn"
                  :class="{ active: activeChannel === ch.id }"
                  @click="activeChannel = ch.id"
                >
                  <span class="channel-badge" :style="{ background: ch.color }">{{ ch.abbr }}</span>
                  <span class="channel-name">{{ ch.name }}</span>
                </button>
              </div>
              <div class="livetv-player">
                <iframe
                  v-if="currentChannelUrl"
                  :src="currentChannelUrl"
                  :key="activeChannel"
                  frameborder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowfullscreen
                  class="livetv-iframe"
                ></iframe>
                <div v-else class="livetv-placeholder">
                  <SvgIcon name="tv" :size="48" />
                  <p>{{ $t('common.selectOption') }}</p>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </teleport>

      <!-- Alerts Panel -->
      <div class="alerts-panel">
        <div class="panel-header">
          <h2 class="panel-title">{{ $t('dashboard.alertsPanel') }}</h2>
          <span class="alert-count">{{ alerts.length }}</span>
        </div>
        <div class="alerts-list">
          <div v-if="alertsLoading" class="loading-state">
            <div class="spinner"></div>
          </div>
          <div v-else-if="!alerts.length" class="empty-state">
            {{ $t('dashboard.noAlerts') }}
          </div>
          <div
            v-for="alert in alerts"
            :key="alert.id"
            class="alert-item"
          >
            <div class="alert-top">
              <StatusBadge :status="alert.severity" size="sm" />
              <span class="alert-time">{{ formatTime(alert.created_at) }}</span>
            </div>
            <div class="alert-title">{{ alert.title }}</div>
            <div class="alert-desc">{{ truncate(alert.description, 100) }}</div>
            <button
              v-if="!alert.acknowledged"
              class="ack-btn"
              @click="acknowledgeAlert(alert.id)"
            >
              {{ $t('dashboard.acknowledge') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import StatCard from '../components/common/StatCard.vue'
import SvgIcon from '../components/common/SvgIcon.vue'
import MapView from '../components/common/MapView.vue'
import ErrorBanner from '../components/common/ErrorBanner.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import { dashboardApi, disastersApi, alertsApi, inventoryApi, requestsApi, shipmentsApi, intelligenceApi } from '../api/client'
import { useErrorHandler } from '../composables/useErrorHandler'

const { error, handleError, clearError } = useErrorHandler()

const stats = ref({})
const disasters = ref([])
const warehouses = ref([])
const alerts = ref([])
const alertsLoading = ref(true)
const liveAlerts = ref([])

const newsItems = ref([])
const newsLoading = ref(true)
const tickerPaused = ref(false)
const availableFeeds = ref([])
const activeFeedIds = ref(['reliefweb', 'icrc', 'gdacs'])

const showLiveTV = ref(false)
const activeChannel = ref(null)

const liveChannels = [
  { id: 'aljazeera', name: 'Al Jazeera English', abbr: 'AJ', color: '#d2a44e', embedUrl: 'https://www.youtube.com/embed/gCNeDWCI0vo?autoplay=1' },
  { id: 'france24', name: 'France 24 English', abbr: 'F24', color: '#003d7d', embedUrl: 'https://embed.france24.com/en/live' },
  { id: 'dw', name: 'DW News', abbr: 'DW', color: '#00a5e5', embedUrl: 'https://www.youtube.com/embed/LuKwFajn37U?autoplay=1' },
  { id: 'sky', name: 'Sky News', abbr: 'SKY', color: '#c40000', embedUrl: 'https://www.youtube.com/embed/XOacA3RYrXk?autoplay=1' },
  { id: 'abc-au', name: 'ABC News Australia', abbr: 'ABC', color: '#003c71', embedUrl: 'https://www.youtube.com/embed/vOTiJkg1voo?autoplay=1' },
  { id: 'ndtv', name: 'NDTV 24x7', abbr: 'NDTV', color: '#e41e26', embedUrl: 'https://www.youtube.com/embed/DFOYoLGnVBc?autoplay=1' },
]

const currentChannelUrl = computed(() => {
  const ch = liveChannels.find(c => c.id === activeChannel.value)
  return ch?.embedUrl || null
})

const tickerFeeds = computed(() => {
  return availableFeeds.value.filter(f => f.category !== 'news')
})

const mapCenter = ref([20, 0])
const mapZoom = ref(2)
const crisisAlert = ref(null)
const seenAlertIds = ref(new Set())
let crisisPollTimer = null

const showMapFilters = ref(false)
const mapLayerFlags = ref({ disasters: true, warehouses: true, liveAlerts: true })
const mapAlertLevelFlags = ref({ red: true, orange: true, green: true })
const mapEventTypeFlags = ref({ EQ: true, FL: true, WF: true, TC: true, DR: true, VO: true, other: true })

const mapLayers = [
  { id: 'disasters', label: 'Disasters', color: '#e74c3c' },
  { id: 'warehouses', label: 'Warehouses', color: '#1e3a5f' },
  { id: 'liveAlerts', label: 'Live GDACS', color: '#27ae60' },
]
const alertLevels = [
  { id: 'red', label: 'Red', color: '#e74c3c' },
  { id: 'orange', label: 'Orange', color: '#e8913a' },
  { id: 'green', label: 'Green', color: '#27ae60' },
]
const eventTypes = [
  { id: 'EQ', label: 'Earthquake', icon: '~' },
  { id: 'FL', label: 'Flood', icon: '~' },
  { id: 'WF', label: 'Wildfire', icon: '~' },
  { id: 'TC', label: 'Cyclone', icon: '~' },
  { id: 'DR', label: 'Drought', icon: '~' },
  { id: 'VO', label: 'Volcano', icon: '~' },
  { id: 'other', label: 'Other', icon: '~' },
]

const activeFilterCount = computed(() => {
  let off = 0
  Object.values(mapLayerFlags.value).forEach(v => { if (!v) off++ })
  Object.values(mapAlertLevelFlags.value).forEach(v => { if (!v) off++ })
  Object.values(mapEventTypeFlags.value).forEach(v => { if (!v) off++ })
  return off
})

const activePanel = ref(null)
const panelLoading = ref(false)
const detailDisasters = ref([])
const detailRequests = ref([])
const detailShipments = ref([])
const detailAlerts = ref([])

const panelTitle = computed(() => {
  const titles = {
    disasters: 'Active Disasters',
    requests: 'Pending Supply Requests',
    shipments: 'In-Transit Shipments',
    alerts: 'Active Alerts'
  }
  return titles[activePanel.value] || ''
})

async function togglePanel(panel) {
  if (activePanel.value === panel) {
    activePanel.value = null
    return
  }
  activePanel.value = panel
  panelLoading.value = true
  try {
    if (panel === 'disasters') {
      const { data } = await disastersApi.list('active')
      detailDisasters.value = data.disasters || data || []
    } else if (panel === 'requests') {
      const { data } = await requestsApi.list('pending')
      detailRequests.value = data.requests || data || []
    } else if (panel === 'shipments') {
      const { data } = await shipmentsApi.list()
      const all = data.shipments || data || []
      detailShipments.value = all.filter(s => s.status === 'in_transit' || s.status === 'shipped')
    } else if (panel === 'alerts') {
      const { data } = await alertsApi.list()
      detailAlerts.value = (data.alerts || data || []).filter(a => !a.acknowledged)
    }
  } catch (e) {
    handleError(e, 'Failed to load detail')
  } finally {
    panelLoading.value = false
  }
}

const severityColors = {
  catastrophic: '#e74c3c',
  major: '#e8913a',
  moderate: '#f39c12',
  minor: '#3498db'
}

function formatPop(n) {
  if (!n) return '—'
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(0) + 'K'
  return n.toLocaleString()
}

const alertLevelColors = {
  red: '#e74c3c',
  orange: '#e8913a',
  green: '#27ae60'
}

const mapMarkers = computed(() => {
  const result = []

  if (mapLayerFlags.value.disasters) {
    disasters.value
      .filter(d => d.latitude && d.longitude)
      .forEach(d => {
        const color = severityColors[d.severity] || '#e74c3c'
        const isActive = d.status === 'active'
        result.push({
          lat: d.latitude,
          lng: d.longitude,
          label: d.name,
          color,
          radius: d.severity === 'catastrophic' ? 12 : d.severity === 'major' ? 10 : 8,
          pulse: isActive,
          popup: `<div style="min-width:180px"><strong style="font-size:13px">${d.name}</strong><br/><span style="display:inline-block;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;color:#fff;background:${color};margin:4px 0">${(d.severity || '').toUpperCase()}</span> <span style="font-size:11px;color:#888">${(d.disaster_type || '').replace(/_/g, ' ')}</span><br/><span style="font-size:12px">Affected: <strong>${formatPop(d.affected_population)}</strong></span><br/><span style="font-size:11px;color:#888">${d.country || ''}${d.region ? ' — ' + d.region : ''}</span></div>`
        })
      })
  }

  if (mapLayerFlags.value.liveAlerts) {
    liveAlerts.value
      .filter(a => {
        if (a.lat == null || a.lng == null) return false
        if (!mapAlertLevelFlags.value[a.alert_level]) return false
        const etype = a.event_type || ''
        const knownTypes = ['EQ', 'FL', 'WF', 'TC', 'DR', 'VO']
        const typeKey = knownTypes.includes(etype) ? etype : 'other'
        if (!mapEventTypeFlags.value[typeKey]) return false
        return true
      })
      .forEach(a => {
        const color = alertLevelColors[a.alert_level] || '#27ae60'
        result.push({
          lat: a.lat,
          lng: a.lng,
          label: a.title,
          color,
          radius: a.alert_level === 'red' ? 10 : a.alert_level === 'orange' ? 8 : 6,
          pulse: a.alert_level === 'red',
          popup: `<div style="min-width:180px"><strong style="font-size:13px">${escapeHtml(a.title)}</strong><br/><span style="display:inline-block;padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600;color:#fff;background:${color};margin:4px 0">${(a.alert_level || '').toUpperCase()}</span> <span style="font-size:11px;color:#888">${escapeHtml(a.event_type || '')}</span><br/>${a.country ? '<span style="font-size:12px">' + escapeHtml(a.country) + '</span><br/>' : ''}${a.severity ? '<span style="font-size:11px;color:#888">' + escapeHtml(a.severity) + '</span>' : ''}<br/><span style="font-size:10px;color:#aaa">Source: GDACS Live</span></div>`
        })
      })
  }

  if (mapLayerFlags.value.warehouses) {
    warehouses.value
      .filter(w => w.latitude && w.longitude)
      .forEach(w => {
        result.push({
          lat: w.latitude,
          lng: w.longitude,
          label: w.name,
          color: 'blue',
          radius: 7,
          popup: `<strong>${w.name}</strong><br>${w.location || ''}`
        })
      })
  }

  return result
})

const tickerItems = computed(() => {
  const filtered = newsItems.value.filter(n => activeFeedIds.value.includes(n.feed_id))
  return [...filtered, ...filtered]
})

const tickerDuration = computed(() => Math.max(tickerItems.value.length * 1.2, 15))

function tickerTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const diffH = Math.floor((now - d) / 3600000)
  if (diffH < 1) return 'just now'
  if (diffH < 24) return diffH + 'h ago'
  const diffD = Math.floor(diffH / 24)
  return diffD + 'd ago'
}

async function toggleFeed(feedId) {
  const idx = activeFeedIds.value.indexOf(feedId)
  if (idx >= 0) {
    if (activeFeedIds.value.length <= 1) return
    activeFeedIds.value.splice(idx, 1)
  } else {
    activeFeedIds.value.push(feedId)
  }
  await loadNews()
}

async function loadNews() {
  newsLoading.value = true
  try {
    const { data } = await intelligenceApi.liveNews(activeFeedIds.value.join(','), 20)
    newsItems.value = data.items || []
    if (!availableFeeds.value.length && data.feeds) {
      availableFeeds.value = data.feeds.map(f => ({ id: f.id, name: f.name, category: f.category }))
    }
  } catch (e) {
    handleError(e, 'Failed to load news')
  } finally {
    newsLoading.value = false
  }
}

function escapeHtml(text) {
  if (!text) return ''
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function focusCrisis(alert) {
  if (alert.lat != null && alert.lng != null) {
    mapCenter.value = [alert.lat, alert.lng]
    mapZoom.value = 6
  }
}

function dismissCrisisAlert() {
  crisisAlert.value = null
  resetMapView()
}

function resetMapView() {
  mapCenter.value = [20, 0]
  mapZoom.value = 2
}

async function pollForNewAlerts() {
  try {
    const { data } = await intelligenceApi.liveAlerts()
    const incoming = data.alerts || []

    if (seenAlertIds.value.size === 0) {
      incoming.forEach(a => seenAlertIds.value.add(a.id || a.title))
      liveAlerts.value = incoming
      return
    }

    const newMajor = incoming.filter(a => {
      const id = a.id || a.title
      if (seenAlertIds.value.has(id)) return false
      return a.alert_level === 'red' || a.alert_level === 'orange'
    })

    incoming.forEach(a => seenAlertIds.value.add(a.id || a.title))
    liveAlerts.value = incoming

    if (newMajor.length > 0) {
      const top = newMajor[0]
      crisisAlert.value = top
      focusCrisis(top)
    }
  } catch (e) {
    handleError(e, 'Failed to poll for alerts')
  }
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatDate(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function truncate(text, len) {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}

async function acknowledgeAlert(id) {
  try {
    await alertsApi.acknowledge(id)
    alerts.value = alerts.value.filter(a => a.id !== id)
    detailAlerts.value = detailAlerts.value.filter(a => a.id !== id)
  } catch (e) {
    handleError(e, 'Failed to acknowledge alert')
  }
}

function retryLoad() {
  clearError()
  window.location.reload()
}

onMounted(async () => {
  try {
    const [statsRes, disastersRes, warehousesRes, alertsRes, liveRes] = await Promise.allSettled([
      dashboardApi.stats(),
      disastersApi.list('active'),
      inventoryApi.warehouses(),
      alertsApi.list(),
      intelligenceApi.liveAlerts()
    ])
    if (statsRes.status === 'fulfilled') stats.value = statsRes.value.data || {}
    if (disastersRes.status === 'fulfilled') disasters.value = disastersRes.value.data?.disasters || disastersRes.value.data || []
    if (warehousesRes.status === 'fulfilled') warehouses.value = warehousesRes.value.data?.warehouses || warehousesRes.value.data || []
    if (alertsRes.status === 'fulfilled') alerts.value = alertsRes.value.data?.alerts || alertsRes.value.data || []
    if (liveRes.status === 'fulfilled') {
      const initialAlerts = liveRes.value.data?.alerts || []
      liveAlerts.value = initialAlerts
      initialAlerts.forEach(a => seenAlertIds.value.add(a.id || a.title))
    }
  } catch (e) {
    handleError(e, 'Failed to load dashboard data')
  } finally {
    alertsLoading.value = false
  }

  try {
    const { data: feedData } = await intelligenceApi.newsFeeds()
    if (feedData.feeds) availableFeeds.value = feedData.feeds
  } catch (e) { /* feeds list optional */ }
  await loadNews()

  crisisPollTimer = setInterval(pollForNewAlerts, 60000)
})

onUnmounted(() => {
  if (crisisPollTimer) clearInterval(crisisPollTimer)
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 1100px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 500px) {
  .stats-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}

/* Detail Panel */
.detail-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
  max-height: 500px;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: -20px;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
}

.detail-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.detail-close {
  background: none;
  border: none;
  font-size: 22px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}

.detail-close:hover {
  color: var(--text);
}

.detail-loading {
  display: flex;
  justify-content: center;
  padding: 32px;
}

.detail-empty {
  padding: 24px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 14px;
}

.detail-body {
  max-height: 360px;
  overflow-y: auto;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  transition: background 0.1s;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row:hover {
  background: var(--bg);
}

.row-main {
  flex: 1;
  min-width: 0;
}

.row-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
}

.row-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 4px;
}

.row-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.meta-item {
  font-size: 12px;
  color: var(--text-secondary);
}

.type-label {
  text-transform: capitalize;
  padding: 1px 8px;
  background: var(--bg);
  border-radius: 3px;
  font-weight: 500;
}

.row-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex-shrink: 0;
}

.pop-stat {
  font-size: 12px;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.time-stat {
  font-size: 11px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.ack-btn-sm {
  padding: 3px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.ack-btn-sm:hover {
  border-color: var(--accent);
  color: var(--accent);
}

/* News Ticker */
.ticker-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.ticker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-bottom: 1px solid var(--border);
  gap: 12px;
}

.ticker-label {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.ticker-live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--danger);
  animation: live-pulse 1.5s ease-in-out infinite;
}

@keyframes live-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.ticker-title {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
}

.ticker-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.feed-toggle {
  padding: 2px 8px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.feed-toggle.active {
  border-color: var(--accent);
  color: var(--accent);
  background: rgba(52, 152, 219, 0.08);
}

.feed-toggle:hover {
  border-color: var(--accent);
}

.ticker-pause {
  padding: 2px 6px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text-secondary);
  font-size: 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.ticker-pause:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.ticker-track-wrapper {
  overflow: hidden;
  position: relative;
  height: 36px;
}

.ticker-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: 12px;
  color: var(--text-secondary);
}

.ticker-track {
  display: flex;
  align-items: center;
  gap: 0;
  white-space: nowrap;
  animation: ticker-scroll linear infinite;
  height: 100%;
}

.ticker-track.paused {
  animation-play-state: paused;
}

@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.ticker-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 24px;
  height: 100%;
  text-decoration: none;
  border-right: 1px solid var(--border);
  transition: background 0.15s;
  flex-shrink: 0;
}

.ticker-item:hover {
  background: var(--bg);
}

.ticker-feed-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 3px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  flex-shrink: 0;
  background: var(--primary);
  color: #fff;
}

.feed-reliefweb { background: #026cb6; }
.feed-unocha { background: #0072bc; }
.feed-icrc { background: #c4161c; }
.feed-who { background: #009cde; }
.feed-gdacs { background: #e8913a; }

.ticker-separator {
  width: 1px;
  height: 16px;
  background: var(--border);
  margin: 0 2px;
}

.live-tv-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border: 1px solid var(--danger);
  border-radius: 10px;
  background: rgba(231, 76, 60, 0.08);
  color: var(--danger);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.live-tv-btn:hover {
  background: rgba(231, 76, 60, 0.18);
}

.ticker-headline {
  font-size: 13px;
  color: var(--text);
  font-weight: 500;
  max-width: 500px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ticker-time {
  font-size: 11px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

/* Crisis Alert Banner */
.crisis-alert-banner {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 20px;
  background: linear-gradient(135deg, rgba(231, 76, 60, 0.15), rgba(231, 76, 60, 0.08));
  border: 1px solid var(--danger);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
  animation: crisis-flash 2s ease-in-out 3;
}

.crisis-alert-banner:hover {
  background: linear-gradient(135deg, rgba(231, 76, 60, 0.22), rgba(231, 76, 60, 0.12));
}

@keyframes crisis-flash {
  0%, 100% { border-color: var(--danger); }
  50% { border-color: transparent; }
}

.crisis-alert-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--danger);
  color: #fff;
  flex-shrink: 0;
  animation: crisis-pulse 1.5s ease-in-out infinite;
}

@keyframes crisis-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.4); }
  50% { box-shadow: 0 0 0 10px rgba(231, 76, 60, 0); }
}

.crisis-alert-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.crisis-alert-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--danger);
}

.crisis-alert-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.crisis-alert-location {
  font-size: 12px;
  color: var(--text-secondary);
}

.crisis-alert-focus {
  padding: 6px 16px;
  border: 1px solid var(--danger);
  border-radius: var(--radius-sm);
  background: var(--danger);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: all 0.15s;
}

.crisis-alert-focus:hover {
  background: #c0392b;
}

.crisis-alert-dismiss {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  flex-shrink: 0;
}

.crisis-alert-dismiss:hover {
  color: var(--text);
}

/* Main Content */
.dashboard-main {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 20px;
}

@media (max-width: 1000px) {
  .dashboard-main {
    grid-template-columns: 1fr;
  }
}

.map-panel,
.alerts-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: 0.01em;
}

.alert-count {
  background: var(--danger);
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
  min-width: 22px;
  height: 22px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  font-variant-numeric: tabular-nums;
}

.map-filter-toggle {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.map-filter-toggle:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.filter-count {
  background: var(--accent);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.map-filters {
  display: flex;
  gap: 16px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.filter-group-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-right: 2px;
}

.map-filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  opacity: 0.5;
}

.map-filter-btn.active {
  opacity: 1;
  border-color: var(--text-secondary);
  color: var(--text);
}

.map-filter-btn:hover {
  border-color: var(--accent);
}

.filter-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.filter-icon {
  font-size: 12px;
  line-height: 1;
}

.map-wrapper {
  height: 380px;
}

@media (max-width: 500px) {
  .map-wrapper {
    height: 260px;
  }
}

.alerts-list {
  max-height: 400px;
  overflow-y: auto;
}

.alert-item {
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  transition: background 0.1s ease;
}

.alert-item:hover {
  background: var(--bg);
}

.alert-item:last-child {
  border-bottom: none;
}

.alert-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.alert-time {
  font-size: 11px;
  color: var(--text-secondary);
}

.alert-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text);
  margin-bottom: 4px;
}

.alert-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 8px;
}

.ack-btn {
  padding: 5px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.ack-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--bg);
}

.loading-state,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  color: var(--text-secondary);
  font-size: 14px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Live TV Modal */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.livetv-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.livetv-modal {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  width: 100%;
  max-width: 960px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.livetv-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.livetv-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.livetv-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--danger);
  animation: live-pulse 1.5s ease-in-out infinite;
}

.livetv-heading {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
}

.livetv-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}

.livetv-close:hover {
  color: var(--text);
}

.livetv-channels {
  display: flex;
  gap: 8px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
  overflow-x: auto;
  flex-shrink: 0;
}

.channel-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
  flex-shrink: 0;
}

.channel-btn.active {
  border-color: var(--accent);
  color: var(--text);
  background: rgba(52, 152, 219, 0.08);
  box-shadow: 0 0 0 1px var(--accent);
}

.channel-btn:hover {
  border-color: var(--accent);
  color: var(--text);
}

.channel-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 3px;
  color: #fff;
  letter-spacing: 0.03em;
}

.channel-name {
  font-size: 13px;
}

.livetv-player {
  flex: 1;
  min-height: 0;
  aspect-ratio: 16 / 9;
  max-height: calc(90vh - 140px);
  background: #000;
}

.livetv-iframe {
  width: 100%;
  height: 100%;
  display: block;
}

.livetv-placeholder {
  width: 100%;
  height: 100%;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--text-secondary);
}

.livetv-placeholder p {
  font-size: 14px;
}

@media (max-width: 700px) {
  .livetv-overlay {
    padding: 8px;
  }
  .livetv-channels {
    gap: 6px;
    padding: 8px 12px;
  }
  .channel-btn {
    padding: 6px 10px;
    font-size: 12px;
  }
}
</style>
