import { CRDTDocument, clock, NODE_ID } from './crdt'

const DB_NAME = 'dlscm-offline'
const DB_VERSION = 2

const STORES = {
  supplyRequests: 'supply_requests',
  inventory: 'inventory',
  syncQueue: 'sync_queue',
  crdtState: 'crdt_state',
}

function openDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)

    request.onupgradeneeded = (event) => {
      const db = event.target.result

      if (!db.objectStoreNames.contains(STORES.supplyRequests)) {
        const store = db.createObjectStore(STORES.supplyRequests, { keyPath: 'id', autoIncrement: true })
        store.createIndex('status', 'status', { unique: false })
        store.createIndex('synced', 'synced', { unique: false })
      }

      if (!db.objectStoreNames.contains(STORES.inventory)) {
        const store = db.createObjectStore(STORES.inventory, { keyPath: 'id' })
        store.createIndex('category', 'category', { unique: false })
        store.createIndex('warehouse_id', 'warehouse_id', { unique: false })
      }

      if (!db.objectStoreNames.contains(STORES.syncQueue)) {
        const store = db.createObjectStore(STORES.syncQueue, { keyPath: 'id', autoIncrement: true })
        store.createIndex('type', 'type', { unique: false })
        store.createIndex('created_at', 'created_at', { unique: false })
      }

      if (!db.objectStoreNames.contains(STORES.crdtState)) {
        const store = db.createObjectStore(STORES.crdtState, { keyPath: 'key' })
        store.createIndex('collection', 'collection', { unique: false })
        store.createIndex('updated_at', 'updated_at', { unique: false })
      }
    }

    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

function txPromise(tx) {
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
  })
}

function reqPromise(req) {
  return new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

// ── CRDT operations ──────────────────────────────────────────────────

export async function crdtPut(collection, id, fields) {
  const db = await openDb()
  const key = `${collection}:${id}`
  const tx = db.transaction(STORES.crdtState, 'readwrite')
  const store = tx.objectStore(STORES.crdtState)

  let existing = await reqPromise(store.get(key))
  let doc
  if (existing) {
    doc = CRDTDocument.fromJSON(existing.data)
  } else {
    doc = new CRDTDocument(id)
  }

  const hlc = clock.now()
  for (const [field, value] of Object.entries(fields)) {
    doc.set(field, value, hlc)
  }

  store.put({
    key,
    collection,
    data: doc.toJSON(),
    updated_at: Date.now(),
  })

  await txPromise(tx)
  db.close()

  await addToSyncQueue('crdt_update', {
    collection,
    id,
    doc: doc.toJSON(),
    node: NODE_ID,
  })

  return doc.toPlainObject()
}

export async function crdtGet(collection, id) {
  const db = await openDb()
  const key = `${collection}:${id}`
  const tx = db.transaction(STORES.crdtState, 'readonly')
  const store = tx.objectStore(STORES.crdtState)
  const record = await reqPromise(store.get(key))
  db.close()

  if (!record) return null
  const doc = CRDTDocument.fromJSON(record.data)
  return doc.deleted ? null : doc.toPlainObject()
}

export async function crdtGetAll(collection) {
  const db = await openDb()
  const tx = db.transaction(STORES.crdtState, 'readonly')
  const store = tx.objectStore(STORES.crdtState)
  const index = store.index('collection')
  const records = await reqPromise(index.getAll(collection))
  db.close()

  return records
    .map((r) => CRDTDocument.fromJSON(r.data))
    .filter((doc) => !doc.deleted)
    .map((doc) => doc.toPlainObject())
}

export async function crdtDelete(collection, id) {
  const db = await openDb()
  const key = `${collection}:${id}`
  const tx = db.transaction(STORES.crdtState, 'readwrite')
  const store = tx.objectStore(STORES.crdtState)

  let existing = await reqPromise(store.get(key))
  if (!existing) {
    db.close()
    return
  }

  const doc = CRDTDocument.fromJSON(existing.data)
  doc.markDeleted(clock.now())

  store.put({
    key,
    collection,
    data: doc.toJSON(),
    updated_at: Date.now(),
  })

  await txPromise(tx)
  db.close()

  await addToSyncQueue('crdt_delete', {
    collection,
    id,
    doc: doc.toJSON(),
    node: NODE_ID,
  })
}

export async function crdtMergeRemote(collection, id, remoteDocJson) {
  const db = await openDb()
  const key = `${collection}:${id}`
  const tx = db.transaction(STORES.crdtState, 'readwrite')
  const store = tx.objectStore(STORES.crdtState)

  const remoteDoc = CRDTDocument.fromJSON(remoteDocJson)
  clock.receive(
    remoteDoc.vv.entries[Object.keys(remoteDoc.vv.entries)[0]]
      ? { ts: Date.now(), counter: 0, node: 'remote' }
      : { ts: Date.now(), counter: 0, node: 'remote' }
  )

  let existing = await reqPromise(store.get(key))
  let localDoc
  if (existing) {
    localDoc = CRDTDocument.fromJSON(existing.data)
    localDoc.merge(remoteDoc)
  } else {
    localDoc = remoteDoc
  }

  store.put({
    key,
    collection,
    data: localDoc.toJSON(),
    updated_at: Date.now(),
  })

  await txPromise(tx)
  db.close()

  return localDoc.toPlainObject()
}

// ── Legacy API (backwards compatible) ────────────────────────────────

export async function cacheInventory(items) {
  const db = await openDb()
  const tx = db.transaction(STORES.inventory, 'readwrite')
  const store = tx.objectStore(STORES.inventory)
  store.clear()
  for (const item of items) {
    store.put({ ...item, cached_at: Date.now() })
  }
  await txPromise(tx)
  db.close()
}

export async function getCachedInventory(category) {
  const db = await openDb()
  const tx = db.transaction(STORES.inventory, 'readonly')
  const store = tx.objectStore(STORES.inventory)
  let items
  if (category) {
    const index = store.index('category')
    items = await reqPromise(index.getAll(category))
  } else {
    items = await reqPromise(store.getAll())
  }
  db.close()
  return items
}

export async function saveOfflineRequest(requestData) {
  const db = await openDb()
  const tx = db.transaction(STORES.supplyRequests, 'readwrite')
  const store = tx.objectStore(STORES.supplyRequests)
  const record = {
    ...requestData,
    synced: false,
    created_at: new Date().toISOString(),
  }
  const id = await reqPromise(store.add(record))
  await txPromise(tx)
  db.close()

  await addToSyncQueue('supply_request', { ...record, id })

  return id
}

export async function getOfflineRequests() {
  const db = await openDb()
  const tx = db.transaction(STORES.supplyRequests, 'readonly')
  const store = tx.objectStore(STORES.supplyRequests)
  const items = await reqPromise(store.getAll())
  db.close()
  return items
}

export async function markRequestSynced(id) {
  const db = await openDb()
  const tx = db.transaction(STORES.supplyRequests, 'readwrite')
  const store = tx.objectStore(STORES.supplyRequests)
  const record = await reqPromise(store.get(id))
  if (record) {
    record.synced = true
    store.put(record)
  }
  await txPromise(tx)
  db.close()
}

async function addToSyncQueue(type, data) {
  const db = await openDb()
  const tx = db.transaction(STORES.syncQueue, 'readwrite')
  const store = tx.objectStore(STORES.syncQueue)
  store.add({ type, data, created_at: Date.now() })
  await txPromise(tx)
  db.close()
}

export async function getSyncQueue() {
  const db = await openDb()
  const tx = db.transaction(STORES.syncQueue, 'readonly')
  const store = tx.objectStore(STORES.syncQueue)
  const items = await reqPromise(store.getAll())
  db.close()
  return items
}

export async function removeSyncItem(id) {
  const db = await openDb()
  const tx = db.transaction(STORES.syncQueue, 'readwrite')
  const store = tx.objectStore(STORES.syncQueue)
  store.delete(id)
  await txPromise(tx)
  db.close()
}

export async function syncPendingRequests(apiClient) {
  const queue = await getSyncQueue()
  const results = { synced: 0, failed: 0, conflicts: 0 }

  for (const item of queue) {
    try {
      if (item.type === 'supply_request') {
        await apiClient.post('/requests', item.data)
        await markRequestSynced(item.data.id)
        await removeSyncItem(item.id)
        results.synced++
      } else if (item.type === 'crdt_update' || item.type === 'crdt_delete') {
        const resp = await apiClient.post('/sync/merge', {
          collection: item.data.collection,
          id: item.data.id,
          doc: item.data.doc,
          node: item.data.node,
        })
        if (resp.data?.merged_doc) {
          await crdtMergeRemote(item.data.collection, item.data.id, resp.data.merged_doc)
          results.conflicts++
        }
        await removeSyncItem(item.id)
        results.synced++
      }
    } catch (e) {
      results.failed++
    }
  }

  return results
}

export function isOnline() {
  return navigator.onLine
}

export function onConnectivityChange(callback) {
  const onlineHandler = () => callback(true)
  const offlineHandler = () => callback(false)
  window.addEventListener('online', onlineHandler)
  window.addEventListener('offline', offlineHandler)
  return () => {
    window.removeEventListener('online', onlineHandler)
    window.removeEventListener('offline', offlineHandler)
  }
}
