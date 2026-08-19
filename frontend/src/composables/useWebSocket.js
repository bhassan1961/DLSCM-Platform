import { ref, onMounted, onUnmounted } from 'vue'

const WS_URL = `ws://${window.location.hostname}:5100/ws`

const globalWs = ref(null)
const connected = ref(false)
const listeners = new Map()
let reconnectTimer = null
let reconnectAttempts = 0
const MAX_RECONNECT = 10

function connect() {
  if (globalWs.value?.readyState === WebSocket.OPEN) return

  try {
    const ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      connected.value = true
      reconnectAttempts = 0
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        const handlers = listeners.get(msg.type) || []
        handlers.forEach((fn) => fn(msg.data, msg))
      } catch { /* ignore malformed */ }
    }

    ws.onclose = () => {
      connected.value = false
      globalWs.value = null
      scheduleReconnect()
    }

    ws.onerror = () => {
      ws.close()
    }

    globalWs.value = ws
  } catch {
    scheduleReconnect()
  }
}

function scheduleReconnect() {
  if (reconnectAttempts >= MAX_RECONNECT) return
  const delay = Math.min(1000 * 2 ** reconnectAttempts, 30000)
  reconnectAttempts++
  clearTimeout(reconnectTimer)
  reconnectTimer = setTimeout(connect, delay)
}

export function useWebSocket() {
  onMounted(() => {
    if (!globalWs.value || globalWs.value.readyState !== WebSocket.OPEN) {
      connect()
    }
  })

  function on(eventType, handler) {
    if (!listeners.has(eventType)) {
      listeners.set(eventType, [])
    }
    listeners.get(eventType).push(handler)

    return () => {
      const arr = listeners.get(eventType)
      if (arr) {
        const idx = arr.indexOf(handler)
        if (idx > -1) arr.splice(idx, 1)
      }
    }
  }

  return { connected, on }
}
