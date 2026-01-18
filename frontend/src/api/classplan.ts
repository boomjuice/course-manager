/**
 * ClassPlan API - 开班计划相关接口
 */
import request from './index'
import type { ListResponse, ResponseModel } from '@/types'

// 开班计划列表响应（扁平化字段，由后端enrich返回）
export interface ClassPlan {
  id: number
  name: string
  course_id: number
  teacher_id?: number
  campus_id?: number
  classroom_id?: number
  max_students: number
  current_students: number
  completed_lessons: number
  start_date?: string
  end_date?: string
  status: string
  description?: string
  is_active: boolean
  total_lessons: number
  schedule?: string
  notes?: string
  // 扁平化的关联名称（由后端enrich返回）
  course_name?: string
  teacher_name?: string
  campus_name?: string
  classroom_name?: string
}

export interface ClassPlanCreate {
  name: string
  course_id: number
  teacher_id?: number
  campus_id?: number
  classroom_id?: number
  max_students?: number
  current_students?: number
  total_lessons?: number  // 支持小数课时
  start_date?: string
  end_date?: string
  status?: string
  schedule?: string
  notes?: string
}

export interface ClassPlanUpdate {
  name?: string
  course_id?: number
  teacher_id?: number
  campus_id?: number
  classroom_id?: number
  max_students?: number
  current_students?: number
  total_lessons?: number  // 支持小数课时
  start_date?: string
  end_date?: string
  status?: string
  schedule?: string
  notes?: string
}

// 课程简要信息（用于报名参考）
export interface CourseBriefInfo {
  id: number
  name: string
  unit_price: number  // 课时单价
}

// 开班计划简要信息（下拉列表用）
export interface ClassPlanBrief {
  id: number
  name: string
  course_id: number
  teacher_id?: number  // 主讲教师，排课时自动带出
  classroom_id?: number  // 默认教室，排课时自动带出
  status: string
  current_students: number  // 当前报名人数，用于教室容量校验
  course?: CourseBriefInfo
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

// 开班计划 API
export const getClassPlans = (params?: {
  page?: number
  page_size?: number
  search?: string
  status?: string
  course_id?: number
  teacher_id?: number
  campus_id?: number
  start_date_from?: string  // 开班日期范围起始
  start_date_to?: string    // 开班日期范围截止
}) => request.get<ListResponse<ClassPlan>>('/class-plans', { params }).then(res => res.data)

// 后端用success_response包装数组会变成{items: [...]}格式
export const getAllClassPlans = (activeOnly = true) =>
  request.get<ResponseModel<{items: ClassPlanBrief[]}>>('/class-plans/all', { params: { active_only: activeOnly } }).then(res => res.data.data?.items || [])

export const getClassPlan = (id: number) =>
  request.get<ResponseModel<ClassPlan>>(`/class-plans/${id}`).then(res => res.data.data)

export const createClassPlan = (data: ClassPlanCreate) =>
  request.post<ResponseModel<ClassPlan>>('/class-plans', data).then(res => res.data.data)

export const updateClassPlan = (id: number, data: ClassPlanUpdate) =>
  request.put<ResponseModel<ClassPlan>>(`/class-plans/${id}`, data).then(res => res.data.data)

export const deleteClassPlan = (id: number) =>
  request.delete(`/class-plans/${id}`).then(res => res.data.data)
