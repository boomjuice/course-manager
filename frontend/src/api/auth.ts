/**
 * Authentication API
 */
import apiClient from './index'
import type {
  User,
  LoginRequest,
  LoginResponse,
  TokenResponse,
  PasswordChangeRequest,
  ProfileUpdateRequest,
  SelectCampusRequest
} from '@/types/user'

export const authApi = {
  /**
   * Login with username and password
   * Returns login response with campus selection info
   */
  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post('/auth/login', data)
    // 后端返回的是 {code: 0, message: "success", data: {...}}，需要取 data
    return response.data.data as LoginResponse
  },

  /**
   * Select a campus after login
   * Returns new tokens with campus_id embedded
   */
  async selectCampus(data: SelectCampusRequest): Promise<LoginResponse> {
    const response = await apiClient.post('/auth/select-campus', data)
    return response.data.data as LoginResponse
  },

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    await apiClient.post('/auth/logout')
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await apiClient.post('/auth/refresh', {
      refresh_token: refreshToken
    })
    return response.data.data as TokenResponse
  },

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get('/auth/me')
    return response.data.data as User
  },

  /**
   * Change password
   */
  async changePassword(data: PasswordChangeRequest): Promise<void> {
    await apiClient.put('/auth/password', data)
  },

  /**
   * Update profile
   */
  async updateProfile(data: ProfileUpdateRequest): Promise<User> {
    const response = await apiClient.put('/auth/profile', data)
    return response.data.data as User
  }
}
