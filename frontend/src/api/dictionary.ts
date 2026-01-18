/**
 * Dictionary API - 数据字典相关接口
 */
import request from './index'
import type { ResponseModel } from '@/types'

export interface DictItem {
  id: number
  type_id: number
  value: string
  label: string
  description?: string
  color?: string
  is_default: boolean
  is_active: boolean
  sort_order: number
}

export interface DictType {
  id: number
  code: string
  name: string
  description?: string
  is_system: boolean
  is_active: boolean
  sort_order: number
  items?: DictItem[]
}

export interface DictTypeCreate {
  code: string
  name: string
  description?: string
  is_active?: boolean
  sort_order?: number
  items?: Omit<DictItem, 'id' | 'type_id'>[]
}

export interface DictItemCreate {
  value: string
  label: string
  description?: string
  color?: string
  is_default?: boolean
  is_active?: boolean
  sort_order?: number
}

// Dictionary Type APIs - 后端用success_response包装数组会变成{items: [...]}格式
export const getDictTypes = (includeInactive = false) =>
  request.get<ResponseModel<{items: DictType[]}>>('/dict/types', { params: { include_inactive: includeInactive } }).then(res => res.data.data?.items || [])

export const getDictType = (typeId: number) =>
  request.get<ResponseModel<DictType>>(`/dict/types/${typeId}`).then(res => res.data.data)

export const getDictTypeByCode = (code: string) =>
  request.get<ResponseModel<DictType>>(`/dict/types/code/${code}`).then(res => res.data.data)

export const createDictType = (data: DictTypeCreate) =>
  request.post<ResponseModel<DictType>>('/dict/types', data).then(res => res.data.data)

export const updateDictType = (typeId: number, data: Partial<DictTypeCreate>) =>
  request.put<ResponseModel<DictType>>(`/dict/types/${typeId}`, data).then(res => res.data.data)

export const deleteDictType = (typeId: number) =>
  request.delete(`/dict/types/${typeId}`).then(res => res.data.data)

// Dictionary Item APIs - 后端用success_response包装数组会变成{items: [...]}格式
export const getDictItems = (typeCode: string, activeOnly = true) =>
  request.get<ResponseModel<{items: DictItem[]}>>(`/dict/items/${typeCode}`, { params: { active_only: activeOnly } }).then(res => res.data.data?.items || [])

export const createDictItem = (typeId: number, data: DictItemCreate) =>
  request.post<ResponseModel<DictItem>>(`/dict/types/${typeId}/items`, data).then(res => res.data.data)

export const updateDictItem = (itemId: number, data: Partial<DictItemCreate>) =>
  request.put<ResponseModel<DictItem>>(`/dict/items/${itemId}`, data).then(res => res.data.data)

export const deleteDictItem = (itemId: number) =>
  request.delete(`/dict/items/${itemId}`).then(res => res.data.data)

export const batchCreateDictItems = (typeId: number, items: DictItemCreate[]) =>
  request.post<ResponseModel<{items: DictItem[]}>>(`/dict/types/${typeId}/items/batch`, { items }).then(res => res.data.data?.items || [])

export const reorderDictItems = (typeId: number, itemIds: number[]) =>
  request.post(`/dict/types/${typeId}/items/reorder`, { item_ids: itemIds }).then(res => res.data.data)
