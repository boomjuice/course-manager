/**
 * Scheduler API - 定时任务管理
 */
import request from './index'
import type { ResponseModel } from '@/types'

export interface SchedulerJob {
  id: string
  name: string
  next_run_time: string | null
  trigger: string
}

export interface SchedulerStatus {
  running: boolean
  jobs: SchedulerJob[]
}

/**
 * 获取调度器状态
 */
export function getSchedulerStatus() {
  return request.get<ResponseModel<SchedulerStatus>>('/scheduler/status').then(res => res.data.data)
}

/**
 * 手动执行定时任务
 */
export function runSchedulerTask(taskId: string) {
  return request.post<ResponseModel<{ success: boolean; message: string }>>(`/scheduler/run/${taskId}`).then(res => res.data.data)
}
