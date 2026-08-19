import { ref } from 'vue'

export function useErrorHandler() {
  const error = ref(null)

  function handleError(err, fallbackMessage = 'An error occurred') {
    if (err?.response?.status === 401) {
      error.value = 'Your session has expired. Please log in again.'
      return
    }
    if (err?.response?.status === 429) {
      error.value = 'Too many requests. Please wait a moment and try again.'
      return
    }
    if (err?.response?.data?.detail) {
      error.value = err.response.data.detail
      return
    }
    if (!navigator.onLine) {
      error.value = 'Network error. Check your connection.'
      return
    }
    error.value = fallbackMessage
  }

  function clearError() {
    error.value = null
  }

  return { error, handleError, clearError }
}
