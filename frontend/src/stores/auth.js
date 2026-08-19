import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '../api/client'

const TOKEN_KEY = 'dlscm_access_token'
const REFRESH_KEY = 'dlscm_refresh_token'
const USER_KEY = 'dlscm_user'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))
  const accessToken = ref(localStorage.getItem(TOKEN_KEY) || null)
  const refreshToken = ref(localStorage.getItem(REFRESH_KEY) || null)
  const isLoggedIn = computed(() => !!accessToken.value && !!user.value)

  function setTokens(data) {
    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token
    user.value = data.user
    localStorage.setItem(TOKEN_KEY, data.access_token)
    localStorage.setItem(REFRESH_KEY, data.refresh_token)
    localStorage.setItem(USER_KEY, JSON.stringify(data.user))
  }

  async function login(email, password) {
    const { data } = await authApi.login(email, password)
    setTokens(data)
  }

  async function register(payload) {
    const { data } = await authApi.register(payload)
    setTokens(data)
  }

  async function refresh() {
    if (!refreshToken.value) throw new Error('No refresh token')
    try {
      const { data } = await authApi.refresh(refreshToken.value)
      setTokens(data)
      return data.access_token
    } catch (e) {
      logout()
      throw e
    }
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
    localStorage.removeItem(USER_KEY)
  }

  function getToken() {
    return accessToken.value
  }

  return { user, accessToken, refreshToken, isLoggedIn, login, register, refresh, logout, getToken }
})
