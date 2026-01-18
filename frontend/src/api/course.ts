/**
 * Course API - 课程产品相关接口
 */
import request from './index'
import type { ListResponse, ResponseModel } from '@/types'

// 课程产品接口
export interface CourseProduct {
  id: number
  name: string
  code: string
  subject?: string  // 学科
  grade_level?: string  // 年级
  level?: string  // 难度级别
  description?: string
  unit_price: number  // 课时单价
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CourseProductCreate {
  name: string
  code: string
  subject?: string
  grade_level?: string
  level?: string
  description?: string
  unit_price?: number  // 课时单价
  is_active?: boolean
}

export interface CourseProductUpdate {
  name?: string
  code?: string
  subject?: string
  grade_level?: string
  level?: string
  description?: string
  unit_price?: number  // 课时单价
  is_active?: boolean
}

// 课程产品 API
export const getCourseProducts = (params?: {
  page?: number
  page_size?: number
  search?: string
  subject?: string
  grade_level?: string
  level?: string
  is_active?: boolean
}) => request.get<ListResponse<CourseProduct>>('/courses', { params }).then(res => res.data)

// 获取所有启用的课程（用于下拉选择）
// 注意：后端API是 /courses/active，不接受参数，只返回启用的课程
// 后端用success_response包装数组会变成{items: [...]}格式
export const getAllCourseProducts = (_activeOnly = true) =>
  request.get<ResponseModel<{items: CourseProduct[]}>>('/courses/active').then(res => res.data.data?.items || [])

export const getCourseProduct = (id: number) =>
  request.get<ResponseModel<CourseProduct>>(`/courses/${id}`).then(res => res.data.data)

export const createCourseProduct = (data: CourseProductCreate) =>
  request.post<ResponseModel<CourseProduct>>('/courses', data).then(res => res.data.data)

export const updateCourseProduct = (id: number, data: CourseProductUpdate) =>
  request.put<ResponseModel<CourseProduct>>(`/courses/${id}`, data).then(res => res.data.data)

export const deleteCourseProduct = (id: number) =>
  request.delete(`/courses/${id}`).then(res => res.data.data)
