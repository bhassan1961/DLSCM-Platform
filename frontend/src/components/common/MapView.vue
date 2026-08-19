<template>
  <div class="map-container" ref="mapContainer" role="img" aria-label="Interactive map showing logistics operations, warehouses, and shipment routes">
    <span class="sr-only">Map visualization. Use the data table below for accessible content.</span>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'

const props = defineProps({
  markers: { type: Array, default: () => [] },
  polylines: { type: Array, default: () => [] },
  center: { type: Array, default: () => [20, 0] },
  zoom: { type: Number, default: 3 }
})

const mapContainer = ref(null)
let map = null
let markerLayer = null
let polylineLayer = null

const colorMap = {
  red: '#e74c3c',
  blue: '#1e3a5f',
  green: '#27ae60',
  amber: '#e8913a',
  orange: '#e8913a',
  yellow: '#f39c12'
}

function resolveColor(color) {
  return colorMap[color] || color || '#1e3a5f'
}

function updateMarkers() {
  if (!map || !markerLayer) return
  markerLayer.clearLayers()
  props.markers.forEach(m => {
    if (m.lat == null || m.lng == null) return
    const color = resolveColor(m.color)
    let marker
    if (m.pulse) {
      const size = (m.radius || 10) * 2
      const pulseSize = size + 20
      const icon = L.divIcon({
        className: 'pulse-marker',
        html: `<span class="pulse-ring" style="width:${pulseSize}px;height:${pulseSize}px;border-color:${color};"></span><span class="pulse-dot" style="width:${size}px;height:${size}px;background:${color};"></span>`,
        iconSize: [pulseSize, pulseSize],
        iconAnchor: [pulseSize / 2, pulseSize / 2]
      })
      marker = L.marker([m.lat, m.lng], { icon })
    } else {
      marker = L.circleMarker([m.lat, m.lng], {
        radius: m.radius || 8,
        fillColor: color,
        color: color,
        weight: 2,
        opacity: 0.9,
        fillOpacity: 0.6
      })
    }
    if (m.popup || m.label) {
      marker.bindPopup(m.popup || m.label)
    }
    markerLayer.addLayer(marker)
  })
}

function updatePolylines() {
  if (!map || !polylineLayer) return
  polylineLayer.clearLayers()
  props.polylines.forEach(p => {
    if (!p.points?.length) return
    const color = resolveColor(p.color)
    const line = L.polyline(p.points, {
      color,
      weight: 3,
      opacity: 0.7,
      dashArray: '8 4'
    })
    polylineLayer.addLayer(line)
  })
}

onMounted(() => {
  if (!mapContainer.value) return
  map = L.map(mapContainer.value).setView(props.center, props.zoom)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(map)
  markerLayer = L.layerGroup().addTo(map)
  polylineLayer = L.layerGroup().addTo(map)
  updateMarkers()
  updatePolylines()

  // Fix Leaflet rendering in flex containers
  setTimeout(() => map?.invalidateSize(), 200)
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})

watch(() => props.markers, updateMarkers, { deep: true })
watch(() => props.polylines, updatePolylines, { deep: true })
watch(() => [props.center, props.zoom], ([c, z]) => {
  if (map && c) map.flyTo(c, z, { duration: 1.5 })
})
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  min-height: 300px;
  border-radius: var(--radius, 8px);
  overflow: hidden;
  border: 1px solid var(--border);
  z-index: 0;
}
</style>

<style>
.pulse-marker {
  background: none !important;
  border: none !important;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pulse-dot {
  position: absolute;
  border-radius: 50%;
  opacity: 0.9;
  box-shadow: 0 0 6px rgba(0, 0, 0, 0.3);
}

.pulse-ring {
  position: absolute;
  border-radius: 50%;
  border: 2px solid;
  opacity: 0;
  animation: pulse-expand 2s ease-out infinite;
}

@keyframes pulse-expand {
  0% { transform: scale(0.5); opacity: 0.8; }
  100% { transform: scale(1.4); opacity: 0; }
}
</style>
