/**
 * User Related Types
 */

export type Role = 'admin' | 'teacher' | 'student'

export interface User {
  id: number
  username: string
  email?: string
  phone?: string
  role: Role
  is_active: boolean
  is_online: boolean
  last_login?: string
  avatar?: string
  created_time: string
  updated_time?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface CampusOption {
  id: number
  name: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  need_select_campus: boolean
  available_campuses: CampusOption[]
  current_campus_id: number | null
}

export interface SelectCampusRequest {
  campus_id: number
}

export interface PasswordChangeRequest {
  old_password: string
  new_password: string
}

export interface UserCreate {
  username: string
  email?: string
  phone?: string
  password: string
  role: Role
  is_active?: boolean
  avatar?: string
}

export interface UserUpdate {
  username?: string
  email?: string
  phone?: string
  role?: Role
  is_active?: boolean
  avatar?: string
}

export interface LoginLog {
  id: number
  user_id: number
  login_time: string
  ip_address?: string
  user_agent?: string
  status: 'success' | 'failed'
  fail_reason?: string
}

export interface ProfileUpdateRequest {
  email?: string
  phone?: string
  avatar?: string
}
