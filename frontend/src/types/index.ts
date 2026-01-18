/**
 * Type Definitions Entry Point
 */

export * from './user'

// Common API Response Types

/**
 * 统一 API 响应格式 (对应后端 ResponseModel)
 * - code: 0 成功，非0 失败
 * - message: 响应消息
 * - data: 业务数据 (dict 类型)
 * - total/page/page_size: 分页信息
 */
export interface ResponseModel<T = unknown> {
  code: number
  message: string
  data?: T
  total?: number
  page?: number
  page_size?: number
}

/**
 * 分页列表响应 (data 中包含 items, total, page, page_size)
 */
export interface ListResponse<T> extends ResponseModel<{
  items: T[]
  total: number
  page: number
  page_size: number
}> {
}
