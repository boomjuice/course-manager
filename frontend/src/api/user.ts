/**
 * User API - 用户管理相关接口
 */
import request from './index'
import type { ListResponse, ResponseModel } from '@/types'

export interface User {
  id: number
  username: string
  email?: string
  nickname?: string
  phone?: string
  role: string  // 兼容旧版：admin/teacher/student
  role_id?: number  // 新版RBAC角色ID
  role_code?: string  // 角色编码：super_admin/campus_admin/teacher/student
  role_name?: string  // 角色名称
  campus_id?: number  // 所属校区（校区管理员/教师/学生需要）
  campus_name?: string  // 校区名称
  is_active: boolean
  is_online?: boolean
  avatar?: string
  last_login?: string
  created_time: string  // 审计字段：创建时间
  updated_time?: string  // 审计字段：更新时间
}

export interface UserCreate {
  username: string
  password: string
  email?: string
  nickname?: string
  phone?: string
  role?: string  // 兼容旧版
  role_id?: number  // 新版RBAC
  campus_id?: number  // 校区ID
  is_active?: boolean
}

export interface UserUpdate {
  email?: string
  nickname?: string
  phone?: string
  role?: string  // 兼容旧版
  role_id?: number  // 新版RBAC
  campus_id?: number  // 校区ID
  is_active?: boolean
}

export interface LoginLog {
  id: number
  user_id: number
  username?: string  // For global log list
  ip_address?: string
  user_agent?: string
  login_time: string
  status: string  // success/failed
  fail_reason?: string
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// 用户 API
export const getUsers = (params?: {
  page?: number
  page_size?: number
  role?: string
  is_active?: boolean
  is_online?: boolean
  search?: string
}) => request.get<ListResponse<User>>('/users', { params }).then(res => res.data)

export const getUser = (id: number) =>
  request.get<ResponseModel<User>>(`/users/${id}`).then(res => res.data.data)

export const createUser = (data: UserCreate) =>
  request.post<ResponseModel<User>>('/users', data).then(res => res.data.data)

export const updateUser = (id: number, data: UserUpdate) =>
  request.put<ResponseModel<User>>(`/users/${id}`, data).then(res => res.data.data)

export const deleteUser = (id: number) =>
  request.delete(`/users/${id}`).then(res => res.data.data)

export const resetUserPassword = (id: number, newPassword: string) =>
  request.post(`/users/${id}/reset-password`, { new_password: newPassword }).then(res => res.data.data)

export const getUserLoginLogs = (userId: number, params?: {
  page?: number
  page_size?: number
}) => request.get<ListResponse<LoginLog>>(`/users/${userId}/login-logs`, { params }).then(res => res.data)

// 获取所有登录日志
export const getLoginLogs = (params?: {
  page?: number
  page_size?: number
  user_id?: number
  status?: string  // success/failed
  search?: string  // Search by username/IP
}) => request.get<ListResponse<LoginLog>>('/login-logs', { params }).then(res => res.data)
