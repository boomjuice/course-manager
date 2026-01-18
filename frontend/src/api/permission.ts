/**
 * Permission API
 */
import apiClient from './index'
import type { ListResponse, ResponseModel } from '@/types'
import type {
  ResourceWithPermissions,
  Role,
  RoleWithPermissions,
  RoleCreate,
  RoleUpdate,
  RolePermissionUpdate,
  UserPermissionInfo
} from '@/types/permission'

export const permissionApi = {
  /**
   * 获取所有资源模块及权限
   * 后端用success_response包装数组会变成{items: [...]}格式
   */
  getResources: async (): Promise<ResourceWithPermissions[]> => {
    const response = await apiClient.get<ResponseModel<{items: ResourceWithPermissions[]}>>('/permissions/resources')
    return response.data.data?.items || []
  },

  /**
   * 获取角色列表
   */
  getRoles: async (params?: {
    page?: number
    page_size?: number
    is_active?: boolean
  }): Promise<ListResponse<Role>> => {
    const response = await apiClient.get<ListResponse<Role>>('/permissions/roles', { params })
    return response.data
  },

  /**
   * 获取角色详情（含权限）
   */
  getRoleById: async (roleId: number): Promise<RoleWithPermissions> => {
    const response = await apiClient.get<ResponseModel<RoleWithPermissions>>(`/permissions/roles/${roleId}`)
    return response.data.data!
  },

  /**
   * 创建角色
   */
  createRole: async (data: RoleCreate): Promise<Role> => {
    const response = await apiClient.post<ResponseModel<Role>>('/permissions/roles', data)
    return response.data.data!
  },

  /**
   * 更新角色
   */
  updateRole: async (roleId: number, data: RoleUpdate): Promise<Role> => {
    const response = await apiClient.put<ResponseModel<Role>>(`/permissions/roles/${roleId}`, data)
    return response.data.data!
  },

  /**
   * 更新角色权限
   */
  updateRolePermissions: async (roleId: number, data: RolePermissionUpdate): Promise<void> => {
    await apiClient.put(`/permissions/roles/${roleId}/permissions`, data)
  },

  /**
   * 删除角色
   */
  deleteRole: async (roleId: number): Promise<void> => {
    await apiClient.delete(`/permissions/roles/${roleId}`)
  },

  /**
   * 获取当前用户权限信息
   */
  getCurrentUserPermissions: async (): Promise<UserPermissionInfo> => {
    const response = await apiClient.get<ResponseModel<UserPermissionInfo>>('/permissions/current')
    return response.data.data!
  }
}
