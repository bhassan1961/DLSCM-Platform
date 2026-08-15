import { ref } from 'vue'
import { defineStore } from 'pinia'

let nextId = 1

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref([])

  function add(message, type = 'info') {
    const id = nextId++
    items.value.push({ id, message, type })
    setTimeout(() => remove(id), 5000)
  }

  function remove(id) {
    items.value = items.value.filter(n => n.id !== id)
  }

  return { items, add, remove }
})
