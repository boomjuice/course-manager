/**
 * Student API - 学生管理相关接口
 */
import request from './index'
import type { ListResponse, ResponseModel } from '@/types'

// 学生接口
export interface Student {
  id: number
  name: string
  phone?: string
  gender?: string
  birthday?: string
  grade?: string
  school?: string
  parent_name?: string
  parent_phone?: string
  address?: string
  source?: string
  subject_levels?: string[]  // 科目水平标签（格式: subject:level）
  learning_goals?: string[]  // 学习目标
  status: string
  total_hours: number    // 总购买课时
  remaining_hours: number  // 剩余课时
  total_paid: number
  remark?: string
  created_time: string
  updated_time: string
}

export interface StudentCreate {
  name: string
  phone?: string
  gender?: string
  birthday?: string
  grade?: string
  school?: string
  parent_name?: string
  parent_phone?: string
  address?: string
  source?: string
  subject_levels?: string[]
  learning_goals?: string[]
  status?: string
  remark?: string
}

export interface StudentUpdate {
  name?: string
  phone?: string
  gender?: string
  birthday?: string
  grade?: string
  school?: string
  parent_name?: string
  parent_phone?: string
  address?: string
  source?: string
  subject_levels?: string[]
  learning_goals?: string[]
  status?: string
  remark?: string
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

// 学生 API
export const getStudents = (params?: {
  page?: number
  page_size?: number
  search?: string
  status?: string
  grade?: string
  source?: string
}) => request.get<ListResponse<Student>>('/students', { params }).then(res => res.data)

// 后端用success_response包装数组会变成{items: [...]}格式
export const getAllStudents = (activeOnly = true) =>
  request.get<ResponseModel<{items: Student[]}>>('/students/all', { params: { active_only: activeOnly } }).then(res => res.data.data?.items || [])

export const getStudent = (id: number) =>
  request.get<ResponseModel<Student>>(`/students/${id}`).then(res => res.data.data)

export const createStudent = (data: StudentCreate) =>
  request.post<ResponseModel<Student>>('/students', data).then(res => res.data.data)

export const updateStudent = (id: number, data: StudentUpdate) =>
  request.put<ResponseModel<Student>>(`/students/${id}`, data).then(res => res.data.data)

export const deleteStudent = (id: number) =>
  request.delete(`/students/${id}`).then(res => res.data.data)
