/**
 * Dashboard API - 仪表盘统计接口
 */
import request from './index'
import type { ResponseModel } from '@/types'

export interface DashboardStats {
  active_students: number
  total_teachers: number
  active_class_plans: number
  total_courses: number
  total_enrollments: number
  recent_enrollments: number
}

// 趋势数据点
export interface TrendDataPoint {
  date: string
  count: number
  amount: number
}

// 班级报名统计
export interface ClassPlanEnrollmentStat {
  class_plan_id: number
  class_plan_name: string
  enrollment_count: number
  total_amount: number
}

// 图表数据响应
export interface ChartDataResponse {
  enrollment_trend: TrendDataPoint[]
  class_plan_stats: ClassPlanEnrollmentStat[]
}

// Dashboard API
export const getDashboardStats = () =>
  request.get<ResponseModel<DashboardStats>>('/dashboard/stats').then(res => res.data.data)

// 获取图表数据
export const getChartData = (days: number = 30) =>
  request.get<ResponseModel<ChartDataResponse>>('/dashboard/charts', { params: { days } }).then(res => res.data.data)

// ==================== 通用类型 ====================

export interface KpiCard {
  label: string
  value: number | string
  unit?: string
  trend?: number
  is_time_filtered: boolean
}

// 通用趋势数据点（用于角色仪表盘）
export interface RoleTrendDataPoint {
  date: string
  value: number
  label?: string
}

export interface DistributionItem {
  name: string
  value: number
  color?: string
}

export interface TimeRangeParams {
  start_date?: string
  end_date?: string
  campus_id?: number
}

// ==================== 学生仪表盘 ====================

export interface StudentScheduleItem {
  schedule_id: number
  date: string
  start_time: string
  end_time: string
  class_name: string
  course_name: string
  teacher_name: string
  classroom?: string
}

export interface StudentEnrollmentItem {
  enrollment_id: number
  class_plan_id: number
  class_name: string
  course_name: string
  teacher_name: string
  status: string
  purchased_hours: number
  used_hours: number
  remaining_hours: number
}

export interface StudentDashboardOverview {
  kpi_cards: KpiCard[]
  upcoming_schedules: StudentScheduleItem[]
}

export interface StudentDashboardCourses {
  enrollments: StudentEnrollmentItem[]
}

export interface StudentDashboardRecords {
  attendance_stats: {
    total: number
    normal: number
    leave: number
    absent: number
    rate: number
  }
  attendance_records: Array<{
    date: string
    class_name: string
    status: string
    notes?: string
  }>
  lesson_records: Array<{
    date: string
    class_name: string
    hours: number
    type: string
    notes?: string
  }>
  lesson_trend: RoleTrendDataPoint[]
}

// Student Dashboard API
export const getStudentDashboard = () =>
  request.get<ResponseModel<StudentDashboardOverview>>('/dashboard/student').then(res => res.data.data)

export const getStudentCourses = () =>
  request.get<ResponseModel<StudentDashboardCourses>>('/dashboard/student/courses').then(res => res.data.data)

export const getStudentRecords = (params?: TimeRangeParams) =>
  request.get<ResponseModel<StudentDashboardRecords>>('/dashboard/student/records', { params }).then(res => res.data.data)

// ==================== 教师仪表盘 ====================

export interface TeacherScheduleItem {
  schedule_id: number
  date: string
  start_time: string
  end_time: string
  class_name: string
  classroom?: string
  student_count: number
}

export interface TeacherClassItem {
  class_plan_id: number
  class_name: string
  course_name: string
  status: string
  current_students: number
  max_students: number
  completed_lessons: number
  total_lessons: number
  occupancy_rate: number
}

export interface TeacherDashboardOverview {
  kpi_cards: KpiCard[]
  upcoming_schedules: TeacherScheduleItem[]
}

export interface TeacherDashboardClasses {
  classes: TeacherClassItem[]
  student_attendance: Array<{
    class_name: string
    total_students: number
    attendance_rate: number
    leave_rate: number
    absent_rate: number
  }>
  total_students: number
}

export interface TeacherDashboardIncome {
  kpi_cards: KpiCard[]
  lesson_trend: RoleTrendDataPoint[]
  income_by_class: DistributionItem[]
}

// Teacher Dashboard API
export const getTeacherDashboard = () =>
  request.get<ResponseModel<TeacherDashboardOverview>>('/dashboard/teacher').then(res => res.data.data)

export const getTeacherClasses = (params?: TimeRangeParams) =>
  request.get<ResponseModel<TeacherDashboardClasses>>('/dashboard/teacher/classes', { params }).then(res => res.data.data)

export const getTeacherIncome = (params?: TimeRangeParams) =>
  request.get<ResponseModel<TeacherDashboardIncome>>('/dashboard/teacher/income', { params }).then(res => res.data.data)

// ==================== 管理员仪表盘 ====================

export interface AdminDashboardOverview {
  kpi_cards: KpiCard[]
  enrollment_trend: RoleTrendDataPoint[]
  revenue_trend: RoleTrendDataPoint[]
  campus_comparison?: DistributionItem[]
}

export interface AdminDashboardStudents {
  kpi_cards: KpiCard[]
  status_distribution: DistributionItem[]
  source_distribution: DistributionItem[]
  grade_distribution: DistributionItem[]
  new_student_trend: RoleTrendDataPoint[]
}

export interface AdminDashboardTeachers {
  kpi_cards: KpiCard[]
  status_distribution: DistributionItem[]
  subject_distribution: DistributionItem[]
  workload_ranking: Array<{
    rank: number
    name: string
    value: number
    extra?: string
  }>
}

export interface AdminDashboardClasses {
  kpi_cards: KpiCard[]
  status_distribution: DistributionItem[]
  occupancy_distribution: DistributionItem[]
  subject_distribution: DistributionItem[]
  progress_ranking: Array<{
    rank: number
    name: string
    value: number
    extra?: string
  }>
}

export interface AdminDashboardFinance {
  kpi_cards: KpiCard[]
  revenue_trend: RoleTrendDataPoint[]
  revenue_by_subject: DistributionItem[]
  revenue_by_campus?: DistributionItem[]
  consumption_rate_trend: RoleTrendDataPoint[]
}

// Admin Dashboard API
export const getAdminDashboard = (params?: TimeRangeParams) =>
  request.get<ResponseModel<AdminDashboardOverview>>('/dashboard/admin', { params }).then(res => res.data.data)

export const getAdminStudents = (params?: TimeRangeParams) =>
  request.get<ResponseModel<AdminDashboardStudents>>('/dashboard/admin/students', { params }).then(res => res.data.data)

export const getAdminTeachers = (params?: TimeRangeParams) =>
  request.get<ResponseModel<AdminDashboardTeachers>>('/dashboard/admin/teachers', { params }).then(res => res.data.data)

export const getAdminClasses = (params?: TimeRangeParams) =>
  request.get<ResponseModel<AdminDashboardClasses>>('/dashboard/admin/classes', { params }).then(res => res.data.data)

export const getAdminFinance = (params?: TimeRangeParams) =>
  request.get<ResponseModel<AdminDashboardFinance>>('/dashboard/admin/finance', { params }).then(res => res.data.data)