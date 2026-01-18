/**
 * Axios Instance Configuration
 */
import axios from 'axios'
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// API Base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response interceptor - Handle errors
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  async (error: AxiosError<{ message?: string; detail?: string }>) => {
    const { response } = error

    if (response) {
      const status = response.status
      const message = response.data?.message || response.data?.detail || '请求失败'

      switch (status) {
        case 401:
          // Unauthorized - Try to refresh token or redirect to login
          const refreshToken = localStorage.getItem('refresh_token')
          if (refreshToken && !error.config?.url?.includes('/auth/refresh')) {
            try {
              const refreshResponse = await apiClient.post('/auth/refresh', {
                refresh_token: refreshToken
              })
              const tokenData = refreshResponse.data.data
              localStorage.setItem('access_token', tokenData.access_token)
              localStorage.setItem('refresh_token', tokenData.refresh_token)
              // Retry original request
              if (error.config) {
                error.config.headers.Authorization = `Bearer ${tokenData.access_token}`
                return apiClient(error.config)
              }
            } catch {
              // Refresh failed, clear auth and redirect
              localStorage.removeItem('access_token')
              localStorage.removeItem('refresh_token')
              router.push({ name: 'Login' })
              ElMessage.error('登录已过期，请重新登录')
            }
          } else {
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            router.push({ name: 'Login' })
            ElMessage.error('请先登录')
          }
          break

        case 403:
          ElMessage.error('权限不足')
          break

        case 404:
          ElMessage.error('资源不存在')
          break

        case 409:
          ElMessage.error(message)
          break

        case 422:
          ElMessage.error('请求参数错误')
          break

        case 500:
          ElMessage.error('服务器错误')
          break

        default:
          ElMessage.error(message)
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时')
    } else {
      ElMessage.error('网络错误')
    }

    return Promise.reject(error)
  }
)

export default apiClient
