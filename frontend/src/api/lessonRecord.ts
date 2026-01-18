/**
 * 课时消耗记录 API - 老王写的，别瞎改
 */
import request from './index'
import type { ListResponse } from '@/types'

export interface LessonRecord {
  id: number
  enrollment_id: number
  schedule_id: number | null
  record_date: string
  hours: number
  type: string
  notes: string | null
  created_time: string
  student_name: string | null
  class_plan_name: string | null
  teacher_name: string | null
  schedule_date: string | null
}

export interface LessonRecordListResponse {
  items: LessonRecord[]
  total: number
  page: number
  page_size: number
}

/**
 * 根据报名ID获取课时消耗记录
 */
export function getLessonRecordsByEnrollment(
  enrollmentId: number,
  params?: { page?: number; page_size?: number }
) {
  return request.get<ListResponse<LessonRecord>>(
    `/lesson-records/by-enrollment/${enrollmentId}`,
    { params }
  ).then(res => res.data)
}

/**
 * 根据学生ID获取课时消耗记录
 */
export function getLessonRecordsByStudent(
  studentId: number,
  params?: { page?: number; page_size?: number; class_plan_id?: number }
) {
  return request.get<ListResponse<LessonRecord>>(
    `/lesson-records/by-student/${studentId}`,
    { params }
  ).then(res => res.data)
}
