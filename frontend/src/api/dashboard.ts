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
