/**
 * Enrollment API - 报名管理相关接口
 */
import request from './index'
import type { ListResponse, ResponseModel } from '@/types'
import type { Student } from './student'
import type { ClassPlan } from './classplan'

// 报名接口
export interface Enrollment {
  id: number
  student_id: number
  class_plan_id: number
  enroll_date?: string
  paid_amount: number
  purchased_hours: number
  used_hours: number
  scheduled_hours: number  // 已排课时总数
  status: string
  notes?: string
  created_at: string
  updated_at: string
  student?: Pick<Student, 'id' | 'name' | 'phone'>
  class_plan?: Pick<ClassPlan, 'id' | 'name'>
}

export interface EnrollmentCreate {
  student_id: number
  class_plan_id: number
  paid_amount?: number
  purchased_hours?: number
  status?: string
  notes?: string
}

export interface EnrollmentUpdate {
  paid_amount?: number
  purchased_hours?: number
  used_hours?: number
  status?: string
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

// 报名 API
export const getEnrollments = (params?: {
  page?: number
  page_size?: number
  student_id?: number
  class_plan_id?: number
  status?: string
  enroll_date_from?: string  // 报名日期范围起始
  enroll_date_to?: string    // 报名日期范围截止
}) => request.get<ListResponse<Enrollment>>('/enrollments', { params }).then(res => res.data)

export const getEnrollment = (id: number) =>
  request.get<ResponseModel<Enrollment>>(`/enrollments/${id}`).then(res => res.data.data)

export const createEnrollment = (data: EnrollmentCreate) =>
  request.post<ResponseModel<Enrollment>>('/enrollments', data).then(res => res.data.data)

export const updateEnrollment = (id: number, data: EnrollmentUpdate) =>
  request.put<ResponseModel<Enrollment>>(`/enrollments/${id}`, data).then(res => res.data.data)

export const deleteEnrollment = (id: number) =>
  request.delete(`/enrollments/${id}`).then(res => res.data.data)

// 学生课时详情
export interface StudentHoursDetail {
  student_id: number
  student_name: string
  purchased_hours: number  // 该学生购买课时
  used_hours: number       // 该学生已用课时
  scheduled_hours: number  // 班级已排课时（共享）
  available_hours: number  // 该学生可排课时（purchased - used - scheduled）
}

// 班级计划课时统计（包含每个学生详情）
export interface ClassPlanHoursSummary {
  class_plan_id: number
  class_plan_name: string
  class_scheduled_hours: number  // 班级已排课时
  students: StudentHoursDetail[] // 每个学生的课时详情
  total_students: number
  min_available_hours: number    // 全班最小可排课时（按这个来计算最大可排节数）
}

export const getClassPlanHoursSummary = (classPlanId: number) =>
  request.get<ResponseModel<ClassPlanHoursSummary>>(`/enrollments/class-plan/${classPlanId}/hours-summary`).then(res => res.data.data)
