import { ref } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '../api/client'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isLoggedIn = ref(false)

  async function login(email) {
    const { data } = await authApi.login(email)
    user.value = data.user || data
    isLoggedIn.value = true
  }

  function logout() {
    user.value = null
    isLoggedIn.value = false
  }

  return { user, isLoggedIn, login, logout }
})
