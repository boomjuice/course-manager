/**
 * Schedule API - 排课管理相关接口
 */
import request from './index'
import type { ListResponse, ResponseModel } from '@/types'

export interface Schedule {
  id: number
  class_plan_id: number
  teacher_id?: number
  classroom_id?: number
  schedule_date: string
  start_time: string
  end_time: string
  lesson_hours: number
  title?: string
  status: string
  notes?: string
  created_time: string
  updated_time?: string
  class_plan?: { id: number; name: string }
  teacher?: { id: number; name: string }
  classroom?: { id: number; name: string }
}

export interface ScheduleCreate {
  class_plan_id: number | undefined
  teacher_id?: number
  classroom_id?: number
  schedule_date: string
  start_time: string
  end_time: string
  lesson_hours?: number
  title?: string
  notes?: string
}

export interface ScheduleUpdate {
  teacher_id?: number
  classroom_id?: number
  schedule_date?: string
  start_time?: string
  end_time?: string
  lesson_hours?: number
  title?: string
  status?: string
  notes?: string
}

// 时间段配置
export interface TimeSlot {
  weekdays: number[]  // 0=Monday, 6=Sunday
  start_time: string
  end_time: string
}

// 日期范围
export interface DateRange {
  start_date: string
  end_date: string
}

// Batch scheduling types - 支持多时间段和多日期范围
export interface ScheduleBatchCreate {
  class_plan_id: number
  teacher_id?: number
  classroom_id?: number
  date_ranges: DateRange[]  // 多日期范围
  time_slots: TimeSlot[]    // 多时间段配置
  lesson_hours?: number
  title?: string
  notes?: string
  max_count?: number  // 最大创建数量（用于课时限制场景）
}

export interface ScheduleBatchResponse {
  created_count: number
  skipped_count: number
  batch_no?: string  // 批次号，可用于批量删除
  schedules: Schedule[]
}

// 批量创建冲突预览
export interface BatchConflictItem {
  schedule_date: string
  start_time: string
  end_time: string
  conflict_type: 'teacher' | 'classroom'
  conflict_with: string
}

export interface BatchPreviewResponse {
  total_count: number
  conflict_count: number
  conflicts: BatchConflictItem[]
}

export interface BatchDeleteResponse {
  deleted_count: number
  message: string
}

// 批量更新类型
export interface ScheduleBatchUpdate {
  schedule_ids: number[]  // 要更新的排课ID列表
  teacher_id?: number
  classroom_id?: number
  notes?: string
}

export interface BatchUpdateResponse {
  updated_count: number
  message: string
}

// 批量删除类型
export interface ScheduleBatchDelete {
  schedule_ids: number[]  // 要删除的排课ID列表
}

export interface CalendarEvent {
  id: string
  calendarId: string
  title: string
  category: string
  start: string
  end: string
  location?: string
  attendees?: string[]
  state?: string
  backgroundColor?: string
  borderColor?: string
  raw?: {
    schedule_id: number
    class_plan_id: number
    class_plan_name?: string
    teacher_id?: number
    teacher_name?: string
    classroom_id?: number
    classroom_name?: string
    lesson_hours: number
    status: string
    notes?: string
    batch_no?: string  // 批次号，有这个说明是批量创建的
  }
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// Schedule API
export const getSchedules = (params?: {
  page?: number
  page_size?: number
  class_plan_id?: number
  teacher_id?: number
  start_date?: string
  end_date?: string
  status?: string
}) => request.get<ListResponse<Schedule>>('/schedules', { params }).then(res => res.data)

// 后端用success_response包装数组会变成{items: [...]}格式
export const getCalendarEvents = (params: {
  start_date: string
  end_date: string
  class_plan_id?: number
  teacher_id?: number
}) => request.get<ResponseModel<{items: CalendarEvent[]}>>('/schedules/calendar', { params }).then(res => res.data.data?.items || [])

export const getSchedule = (id: number) =>
  request.get<ResponseModel<Schedule>>(`/schedules/${id}`).then(res => res.data.data)

export const createSchedule = (data: ScheduleCreate) =>
  request.post<ResponseModel<Schedule>>('/schedules', data).then(res => res.data.data)

export const updateSchedule = (id: number, data: ScheduleUpdate) =>
  request.put<ResponseModel<Schedule>>(`/schedules/${id}`, data).then(res => res.data.data)

export const deleteSchedule = (id: number) =>
  request.delete(`/schedules/${id}`).then(res => res.data.data)

// Batch scheduling API
export const batchPreviewSchedule = (data: ScheduleBatchCreate) =>
  request.post<ResponseModel<BatchPreviewResponse>>('/schedules/batch/preview', data).then(res => res.data.data)

export const batchCreateSchedule = (data: ScheduleBatchCreate) =>
  request.post<ResponseModel<ScheduleBatchResponse>>('/schedules/batch', data).then(res => res.data.data)

// Batch delete by batch_no
export const batchDeleteSchedule = (batchNo: string) =>
  request.delete<ResponseModel<BatchDeleteResponse>>(`/schedules/batch/${batchNo}`).then(res => res.data.data)

// Batch update by IDs - 按ID列表批量更新
export const batchUpdateSchedules = (data: ScheduleBatchUpdate) =>
  request.put<ResponseModel<BatchUpdateResponse>>('/schedules/batch', data).then(res => res.data.data)

// Batch delete by IDs - 按ID列表批量删除
export const batchDeleteSchedules = (data: ScheduleBatchDelete) =>
  request.post<ResponseModel<{ message: string }>>('/schedules/batch-delete', data).then(res => res.data.data)

// Get all schedules in a batch
// 后端用success_response包装数组会变成{items: [...]}格式
export const getBatchSchedules = (batchNo: string) =>
  request.get<ResponseModel<{items: Schedule[]}>>(`/schedules/batch/${batchNo}`).then(res => res.data.data?.items || [])

// 冲突检测相关
export interface ConflictDetail {
  type: 'teacher' | 'classroom'
  schedule_id: number
  class_plan_name: string
  schedule_date: string
  start_time: string
  end_time: string
  message: string
}

export interface ConflictCheckRequest {
  class_plan_id: number
  teacher_id?: number
  classroom_id?: number
  schedule_date: string
  start_time: string
  end_time: string
  exclude_schedule_id?: number
}

export interface ConflictCheckResponse {
  has_conflict: boolean
  conflicts: ConflictDetail[]
}

// 检测排课冲突
export const checkScheduleConflicts = (data: ConflictCheckRequest) =>
  request.post<ResponseModel<ConflictCheckResponse>>('/schedules/check-conflicts', data).then(res => res.data.data)
