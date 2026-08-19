const NODE_ID = crypto.randomUUID().slice(0, 8)

// Hybrid Logical Clock
class HLC {
  constructor() {
    this.ts = Date.now()
    this.counter = 0
    this.node = NODE_ID
  }

  now() {
    const pt = Date.now()
    if (pt > this.ts) {
      this.ts = pt
      this.counter = 0
    } else {
      this.counter++
    }
    return { ts: this.ts, counter: this.counter, node: this.node }
  }

  receive(remote) {
    const pt = Date.now()
    if (pt > this.ts && pt > remote.ts) {
      this.ts = pt
      this.counter = 0
    } else if (remote.ts > this.ts) {
      this.ts = remote.ts
      this.counter = remote.counter + 1
    } else if (this.ts > remote.ts) {
      this.counter++
    } else {
      this.counter = Math.max(this.counter, remote.counter) + 1
    }
    return { ts: this.ts, counter: this.counter, node: this.node }
  }
}

function compareHLC(a, b) {
  if (a.ts !== b.ts) return a.ts - b.ts
  if (a.counter !== b.counter) return a.counter - b.counter
  return a.node < b.node ? -1 : a.node > b.node ? 1 : 0
}

// Last-Writer-Wins Register
class LWWRegister {
  constructor(value = null, hlc = null) {
    this.value = value
    this.hlc = hlc
  }

  set(value, hlc) {
    if (!this.hlc || compareHLC(hlc, this.hlc) > 0) {
      this.value = value
      this.hlc = hlc
      return true
    }
    return false
  }

  merge(other) {
    if (!this.hlc || (other.hlc && compareHLC(other.hlc, this.hlc) > 0)) {
      this.value = other.value
      this.hlc = other.hlc
      return true
    }
    return false
  }

  toJSON() {
    return { value: this.value, hlc: this.hlc }
  }

  static fromJSON(json) {
    return new LWWRegister(json.value, json.hlc)
  }
}

// Version Vector for tracking sync state per node
class VersionVector {
  constructor(entries = {}) {
    this.entries = { ...entries }
  }

  increment(nodeId) {
    this.entries[nodeId] = (this.entries[nodeId] || 0) + 1
    return this.entries[nodeId]
  }

  get(nodeId) {
    return this.entries[nodeId] || 0
  }

  merge(other) {
    for (const [node, ver] of Object.entries(other.entries)) {
      this.entries[node] = Math.max(this.entries[node] || 0, ver)
    }
  }

  dominates(other) {
    for (const [node, ver] of Object.entries(other.entries)) {
      if ((this.entries[node] || 0) < ver) return false
    }
    return true
  }

  concurrent(other) {
    return !this.dominates(other) && !other.dominates(this)
  }

  toJSON() {
    return { ...this.entries }
  }

  static fromJSON(json) {
    return new VersionVector(json || {})
  }
}

// CRDT Document — a map of LWW fields with a version vector
class CRDTDocument {
  constructor(id, fields = {}, vv = null) {
    this.id = id
    this.fields = {}
    for (const [k, v] of Object.entries(fields)) {
      this.fields[k] = v instanceof LWWRegister ? v : new LWWRegister(v)
    }
    this.vv = vv || new VersionVector()
    this.deleted = false
    this.deleteHLC = null
  }

  set(field, value, hlc) {
    if (!this.fields[field]) {
      this.fields[field] = new LWWRegister()
    }
    const changed = this.fields[field].set(value, hlc)
    if (changed) {
      this.vv.increment(hlc.node)
    }
    return changed
  }

  get(field) {
    return this.fields[field]?.value ?? null
  }

  markDeleted(hlc) {
    if (!this.deleteHLC || compareHLC(hlc, this.deleteHLC) > 0) {
      this.deleted = true
      this.deleteHLC = hlc
      this.vv.increment(hlc.node)
    }
  }

  merge(remote) {
    if (remote.deleted && (!this.deleteHLC || compareHLC(remote.deleteHLC, this.deleteHLC) > 0)) {
      this.deleted = true
      this.deleteHLC = remote.deleteHLC
    }

    for (const [field, reg] of Object.entries(remote.fields)) {
      if (!this.fields[field]) {
        this.fields[field] = new LWWRegister()
      }
      this.fields[field].merge(reg)
    }

    this.vv.merge(remote.vv)
  }

  toPlainObject() {
    const obj = { id: this.id }
    for (const [k, reg] of Object.entries(this.fields)) {
      obj[k] = reg.value
    }
    return obj
  }

  toJSON() {
    const fields = {}
    for (const [k, reg] of Object.entries(this.fields)) {
      fields[k] = reg.toJSON()
    }
    return {
      id: this.id,
      fields,
      vv: this.vv.toJSON(),
      deleted: this.deleted,
      deleteHLC: this.deleteHLC,
    }
  }

  static fromJSON(json) {
    const fields = {}
    for (const [k, v] of Object.entries(json.fields || {})) {
      fields[k] = LWWRegister.fromJSON(v)
    }
    const doc = new CRDTDocument(json.id, {})
    doc.fields = fields
    doc.vv = VersionVector.fromJSON(json.vv)
    doc.deleted = json.deleted || false
    doc.deleteHLC = json.deleteHLC || null
    return doc
  }
}

const clock = new HLC()

export {
  HLC,
  LWWRegister,
  VersionVector,
  CRDTDocument,
  compareHLC,
  clock,
  NODE_ID,
}
