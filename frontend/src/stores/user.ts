import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('authToken'))
  const username = ref(localStorage.getItem('username'))

  const isAuthenticated = computed(() => !!token.value)

  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('authToken', newToken)
  }

  function setUsername(newUsername: string) {
    username.value = newUsername
    localStorage.setItem('username', newUsername)
  }

  function clearAuth() {
    token.value = null
    username.value = null
    localStorage.removeItem('authToken')
    localStorage.removeItem('username')
  }

  return { token, username, isAuthenticated, setToken, setUsername, clearAuth }
})
