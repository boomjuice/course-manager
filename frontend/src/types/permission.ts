/**
 * Permission types for RBAC system
 */

/** 资源模块 */
export interface Resource {
  id: number
  code: string
  name: string
  description?: string
  sort_order: number
  is_active: boolean
}

/** 权限 */
export interface Permission {
  id: number
  resource_id: number
  action: 'read' | 'edit' | 'delete'
  name: string
  description?: string
}

/** 资源及其权限 */
export interface ResourceWithPermissions extends Resource {
  permissions: Permission[]
}

/** 角色 */
export interface Role {
  id: number
  code: string
  name: string
  description?: string
  is_system: boolean
  is_active: boolean
  created_time?: string
}

/** 角色及其权限 */
export interface RoleWithPermissions extends Role {
  permissions: Permission[]
}

/** 创建角色请求 */
export interface RoleCreate {
  code: string
  name: string
  description?: string
  is_active?: boolean
  permission_ids?: number[]
}

/** 更新角色请求 */
export interface RoleUpdate {
  name?: string
  description?: string
  is_active?: boolean
}

/** 更新角色权限请求 */
export interface RolePermissionUpdate {
  permission_ids: number[]
}

/** 用户权限信息（登录后获取） */
export interface UserPermissionInfo {
  role_code: string | null
  role_name: string | null
  campus_id: number | null
  campus_name: string | null
  permissions: string[]  // 格式: "resource:action"
  is_super_admin: boolean
}

/** 权限检查类型 */
export type PermissionAction = 'read' | 'edit' | 'delete'

/** 系统资源编码 */
export type ResourceCode =
  | 'dashboard'
  | 'student'
  | 'teacher'
  | 'course'
  | 'class_plan'
  | 'enrollment'
  | 'schedule'
  | 'campus'
  | 'classroom'
  | 'user'
  | 'dictionary'
  | 'role_permission'
  | 'system'

/** 权限标识符类型 (resource:action) */
export type PermissionKey = `${ResourceCode}:${PermissionAction}`
