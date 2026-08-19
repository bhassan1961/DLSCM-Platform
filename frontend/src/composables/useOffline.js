import { ref, onMounted, onUnmounted } from 'vue'
import {
  isOnline as checkOnline,
  syncPendingRequests,
  getSyncQueue,
  crdtPut,
  crdtGet,
  crdtGetAll,
  crdtDelete,
  crdtMergeRemote,
} from '../services/offlineDb'
import api from '../api/client'

const online = ref(true)
const pendingCount = ref(0)
const syncing = ref(false)
const lastSyncResult = ref(null)

export function useOffline() {
  function handleOnline() {
    online.value = true
    attemptSync()
  }

  function handleOffline() {
    online.value = false
  }

  async function attemptSync() {
    if (!online.value || syncing.value) return
    syncing.value = true
    try {
      const result = await syncPendingRequests(api)
      lastSyncResult.value = result
      if (result.synced > 0) {
        console.log(`Synced ${result.synced} items (${result.conflicts} merges)`)
      }
      await refreshPendingCount()
    } catch (e) {
      console.error('Sync failed:', e)
    } finally {
      syncing.value = false
    }
  }

  async function refreshPendingCount() {
    try {
      const queue = await getSyncQueue()
      pendingCount.value = queue.length
    } catch (e) {
      pendingCount.value = 0
    }
  }

  onMounted(() => {
    online.value = checkOnline()
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    refreshPendingCount()
  })

  onUnmounted(() => {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  })

  return {
    online,
    pendingCount,
    syncing,
    lastSyncResult,
    attemptSync,
    refreshPendingCount,
    crdtPut,
    crdtGet,
    crdtGetAll,
    crdtDelete,
    crdtMergeRemote,
  }
}
