/**
 * Teacher API - 教师管理相关接口
 */
import request from './index'
import type { ListResponse, ResponseModel } from '@/types'

// 教师接口
export interface Teacher {
  id: number
  name: string
  phone?: string
  gender?: string
  education?: string
  major?: string
  subjects?: string[]  // 负责科目（字典值数组）
  grade_levels?: string[]  // 负责年级（字典值数组）
  hire_date?: string
  status: string
  hourly_rate: number
  introduction?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface TeacherCreate {
  name: string
  phone?: string
  gender?: string
  education?: string
  major?: string
  subjects?: string[]
  grade_levels?: string[]
  hire_date?: string
  status?: string
  hourly_rate?: number
  introduction?: string
  notes?: string
}

export interface TeacherUpdate {
  name?: string
  phone?: string
  gender?: string
  education?: string
  major?: string
  subjects?: string[]
  grade_levels?: string[]
  hire_date?: string
  status?: string
  hourly_rate?: number
  introduction?: string
  notes?: string
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

// 教师 API
export const getTeachers = (params?: {
  page?: number
  page_size?: number
  search?: string
  status?: string
  subjects?: string[]
  grade_levels?: string[]
}) => request.get<ListResponse<Teacher>>('/teachers', { params }).then(res => res.data)

// 后端用success_response包装数组会变成{items: [...]}格式
export const getAllTeachers = (activeOnly = true) =>
  request.get<ResponseModel<{items: Teacher[]}>>('/teachers/all', { params: { active_only: activeOnly } }).then(res => res.data.data?.items || [])

export const getTeacher = (id: number) =>
  request.get<ResponseModel<Teacher>>(`/teachers/${id}`).then(res => res.data.data)

export const createTeacher = (data: TeacherCreate) =>
  request.post<ResponseModel<Teacher>>('/teachers', data).then(res => res.data.data)

export const updateTeacher = (id: number, data: TeacherUpdate) =>
  request.put<ResponseModel<Teacher>>(`/teachers/${id}`, data).then(res => res.data.data)

export const deleteTeacher = (id: number) =>
  request.delete(`/teachers/${id}`).then(res => res.data.data)
