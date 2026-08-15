<template>
  <div class="map-container" ref="mapContainer"></div>
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
    const circle = L.circleMarker([m.lat, m.lng], {
      radius: m.radius || 8,
      fillColor: color,
      color: color,
      weight: 2,
      opacity: 0.9,
      fillOpacity: 0.6
    })
    if (m.popup || m.label) {
      circle.bindPopup(m.popup || m.label)
    }
    markerLayer.addLayer(circle)
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
watch(() => props.center, (val) => {
  if (map && val) map.setView(val, props.zoom)
})
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  min-height: 300px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border);
  z-index: 0;
}
</style>
