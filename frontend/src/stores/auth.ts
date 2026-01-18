/**
 * Authentication Store (Pinia)
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { User, LoginRequest, ProfileUpdateRequest, CampusOption, LoginResponse } from '@/types/user'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))

  // Campus selection state
  const needSelectCampus = ref<boolean>(false)
  const availableCampuses = ref<CampusOption[]>([])
  const currentCampusId = ref<number | null>(
    localStorage.getItem('current_campus_id')
      ? parseInt(localStorage.getItem('current_campus_id')!)
      : null
  )

  // Getters
  const isAuthenticated = computed(() => !!accessToken.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isTeacher = computed(() => user.value?.role === 'teacher')
  const isStudent = computed(() => user.value?.role === 'student')
  const currentUser = computed(() => user.value)
  const hasCampusSelected = computed(() => currentCampusId.value !== null || !needSelectCampus.value)

  // Actions
  async function login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await authApi.login(credentials)

    // Store tokens
    accessToken.value = response.access_token
    refreshToken.value = response.refresh_token
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)

    // Store campus selection info
    needSelectCampus.value = response.need_select_campus
    availableCampuses.value = response.available_campuses
    currentCampusId.value = response.current_campus_id

    if (response.current_campus_id) {
      localStorage.setItem('current_campus_id', response.current_campus_id.toString())
    }

    await fetchCurrentUser()

    // Load permissions after login (only if campus is selected or not needed)
    if (!response.need_select_campus) {
      try {
        const { usePermissionStore } = await import('./permission')
        const permissionStore = usePermissionStore()
        await permissionStore.loadPermissions()
      } catch (error) {
        console.error('Failed to load permissions after login:', error)
      }
    }

    return response
  }

  async function selectCampus(campusId: number): Promise<void> {
    const response = await authApi.selectCampus({ campus_id: campusId })

    // Update tokens with new campus_id
    accessToken.value = response.access_token
    refreshToken.value = response.refresh_token
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)

    // Update campus state
    needSelectCampus.value = false
    availableCampuses.value = []
    currentCampusId.value = campusId
    localStorage.setItem('current_campus_id', campusId.toString())

    // Load permissions after campus selection
    try {
      const { usePermissionStore } = await import('./permission')
      const permissionStore = usePermissionStore()
      await permissionStore.loadPermissions()
    } catch (error) {
      console.error('Failed to load permissions after campus selection:', error)
    }
  }

  async function logout(): Promise<void> {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      clearAuth()
    }
  }

  async function fetchCurrentUser(): Promise<void> {
    try {
      user.value = await authApi.getCurrentUser()
    } catch (error) {
      console.error('Failed to fetch current user:', error)
      clearAuth()
    }
  }

  async function refreshAccessToken(): Promise<boolean> {
    if (!refreshToken.value) return false
    try {
      const response = await authApi.refreshToken(refreshToken.value)
      accessToken.value = response.access_token
      refreshToken.value = response.refresh_token
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      return true
    } catch (error) {
      console.error('Token refresh failed:', error)
      clearAuth()
      return false
    }
  }

  async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await authApi.changePassword({ old_password: oldPassword, new_password: newPassword })
  }

  async function updateProfile(data: ProfileUpdateRequest): Promise<void> {
    user.value = await authApi.updateProfile(data)
  }

  function clearAuth(): void {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    needSelectCampus.value = false
    availableCampuses.value = []
    currentCampusId.value = null

    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('current_campus_id')

    // Clear permissions on logout
    import('./permission').then(({ usePermissionStore }) => {
      const permissionStore = usePermissionStore()
      permissionStore.clearPermissions()
    }).catch(() => {
      // Ignore import errors during cleanup
    })
  }

  // Initialize: fetch user if token exists
  async function initialize(): Promise<void> {
    if (accessToken.value) {
      await fetchCurrentUser()
    }
  }

  return {
    // State
    user,
    accessToken,
    refreshToken,
    needSelectCampus,
    availableCampuses,
    currentCampusId,
    // Getters
    isAuthenticated,
    isAdmin,
    isTeacher,
    isStudent,
    currentUser,
    hasCampusSelected,
    // Actions
    login,
    logout,
    selectCampus,
    fetchCurrentUser,
    refreshAccessToken,
    changePassword,
    updateProfile,
    clearAuth,
    initialize
  }
})
