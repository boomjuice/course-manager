/**
 * Student Attendance API - 学生出勤管理
 */
import request from '@/api'
import type { ListResponse, ResponseModel } from '@/types'

// Types
export interface StudentAttendance {
  id: number
  enrollment_id: number
  schedule_id: number
  status: 'normal' | 'leave' | 'absent'
  leave_reason?: string
  apply_time?: string
  deduct_hours: boolean
  notes?: string
}

export interface StudentAttendanceDetail extends StudentAttendance {
  student_name?: string
  schedule_date?: string
  class_plan_name?: string
}

export interface ScheduleAttendanceItem {
  enrollment_id: number
  student_id: number
  student_name?: string
  status: 'normal' | 'leave' | 'absent'
  leave_reason?: string
  apply_time?: string
  attendance_id?: number
}

export interface UpcomingScheduleItem {
  schedule_id: number
  enrollment_id: number
  schedule_date: string
  start_time: string
  end_time: string
  class_plan_name?: string
  title?: string
  attendance_status?: 'normal' | 'leave' | 'absent' | null
  leave_reason?: string
}

export interface AttendanceMarkRequest {
  enrollment_id: number
  schedule_id: number
  status: 'normal' | 'leave' | 'absent'
  leave_reason?: string
  deduct_hours?: boolean
  notes?: string
}

// API Functions

/**
 * Get student's attendance records
 */
export function getStudentAttendances(
  studentId: number,
  params?: { page?: number; page_size?: number; status?: string }
) {
  return request.get<ListResponse<StudentAttendanceDetail>>(
    `/attendances/student/${studentId}`,
    { params }
  ).then(res => res.data)
}

/**
 * Get all students' attendance for a schedule
 */
export function getScheduleAttendances(scheduleId: number) {
  return request.get<ResponseModel<ScheduleAttendanceItem[]>>(
    `/attendances/schedule/${scheduleId}`
  ).then(res => res.data.data)
}

/**
 * Get upcoming schedules for student (for leave application)
 */
export function getUpcomingSchedules(studentId: number, days: number = 7) {
  return request.get<ResponseModel<{ items: UpcomingScheduleItem[] }>>(
    `/attendances/upcoming/${studentId}`,
    { params: { days } }
  ).then(res => res.data.data?.items || [])
}

/**
 * Student applies for leave
 */
export function applyLeave(data: { schedule_id: number; leave_reason: string }) {
  return request.post<ResponseModel<StudentAttendance>>('/attendances/leave', data).then(res => res.data.data)
}

/**
 * Admin applies leave for a student
 */
export function applyLeaveForStudent(
  studentId: number,
  data: { schedule_id: number; leave_reason: string }
) {
  return request.post<ResponseModel<StudentAttendance>>(`/attendances/leave/${studentId}`, data).then(res => res.data.data)
}

/**
 * Mark student attendance (admin)
 */
export function markAttendance(data: AttendanceMarkRequest) {
  return request.post<ResponseModel<StudentAttendance>>('/attendances/mark', data).then(res => res.data.data)
}

/**
 * Batch mark attendance for a schedule
 */
export function batchMarkAttendance(
  scheduleId: number,
  items: AttendanceMarkRequest[]
) {
  return request.post<ResponseModel<StudentAttendance[]>>(
    `/attendances/batch-mark/${scheduleId}`,
    items
  ).then(res => res.data.data)
}
