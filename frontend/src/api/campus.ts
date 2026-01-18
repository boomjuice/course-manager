/**
 * Campus API - 校区和教室相关接口
 */
import request from './index'
import type { ResponseModel } from '@/types'

// 校区接口
export interface Campus {
  id: number
  name: string
  address?: string
  phone?: string
  is_active: boolean
  created_at: string
  updated_at: string
  classroom_count?: number
}

export interface CampusCreate {
  name: string
  address?: string
  phone?: string
  is_active?: boolean
}

export interface CampusUpdate {
  name?: string
  address?: string
  phone?: string
  is_active?: boolean
}

// 教室接口
export interface Classroom {
  id: number
  campus_id: number
  name: string
  capacity?: number
  description?: string
  equipment?: Record<string, string>  // 设备配置：key-value形式
  is_active: boolean
  created_time: string
  updated_time: string
  campus?: Campus
}

export interface ClassroomCreate {
  campus_id: number
  name: string
  capacity?: number
  description?: string
  equipment?: Record<string, string>  // 设备配置：key-value形式
  is_active?: boolean
}

export interface ClassroomUpdate {
  campus_id?: number
  name?: string
  capacity?: number
  description?: string
  equipment?: Record<string, string>  // 设备配置：key-value形式
  is_active?: boolean
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

// 校区 API - 后端用success_response包装数组会变成{items: [...]}格式
export const getCampuses = (params?: {
  include_inactive?: boolean
}) => request.get<ResponseModel<{items: Campus[]}>>('/campuses', { params }).then(res => res.data.data?.items || [])

export const getAllCampuses = (activeOnly = true) =>
  request.get<ResponseModel<{items: Campus[]}>>('/campuses/all', { params: { active_only: activeOnly } }).then(res => res.data.data?.items || [])

export const getCampus = (id: number) =>
  request.get<ResponseModel<Campus>>(`/campuses/${id}`).then(res => res.data.data)

export const createCampus = (data: CampusCreate) =>
  request.post<ResponseModel<Campus>>('/campuses', data).then(res => res.data.data)

export const updateCampus = (id: number, data: CampusUpdate) =>
  request.put<ResponseModel<Campus>>(`/campuses/${id}`, data).then(res => res.data.data)

export const deleteCampus = (id: number) =>
  request.delete(`/campuses/${id}`).then(res => res.data.data)

// 教室 API - 后端用success_response包装数组会变成{items: [...]}格式
export const getClassrooms = (params?: {
  active_only?: boolean
}) => request.get<ResponseModel<{items: Classroom[]}>>('/classrooms', { params }).then(res => res.data.data?.items || [])

export const getAllClassrooms = (campusId?: number, activeOnly = true) =>
  request.get<ResponseModel<{items: Classroom[]}>>('/classrooms/all', {
    params: { campus_id: campusId, active_only: activeOnly }
  }).then(res => res.data.data?.items || [])

export const getClassroom = (id: number) =>
  request.get<ResponseModel<Classroom>>(`/classrooms/${id}`).then(res => res.data.data)

export const createClassroom = (data: ClassroomCreate) =>
  request.post<ResponseModel<Classroom>>('/classrooms', data).then(res => res.data.data)

export const updateClassroom = (id: number, data: ClassroomUpdate) =>
  request.put<ResponseModel<Classroom>>(`/classrooms/${id}`, data).then(res => res.data.data)

export const deleteClassroom = (id: number) =>
  request.delete(`/classrooms/${id}`).then(res => res.data.data)
