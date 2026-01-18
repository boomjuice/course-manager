/**
 * Permission Store (Pinia) - RBAC权限状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { permissionApi } from '@/api/permission'
import type { ResourceCode, PermissionAction, UserPermissionInfo } from '@/types/permission'

export const usePermissionStore = defineStore('permission', () => {
  // State
  const permissions = ref<Set<string>>(new Set())
  const roleCode = ref<string | null>(null)
  const roleName = ref<string | null>(null)
  const campusId = ref<number | null>(null)
  const campusName = ref<string | null>(null)
  const isSuperAdmin = ref(false)
  const isLoaded = ref(false)

  // Getters
  /**
   * 检查是否有指定权限
   * @param resource 资源编码
   * @param action 操作类型
   */
  const hasPermission = computed(() => {
    return (resource: ResourceCode, action: PermissionAction): boolean => {
      // 超级管理员拥有所有权限
      if (isSuperAdmin.value) return true
      return permissions.value.has(`${resource}:${action}`)
    }
  })

  /**
   * 检查是否有读取权限
   */
  const canRead = computed(() => {
    return (resource: ResourceCode): boolean => hasPermission.value(resource, 'read')
  })

  /**
   * 检查是否有编辑权限（包含创建和更新）
   */
  const canEdit = computed(() => {
    return (resource: ResourceCode): boolean => hasPermission.value(resource, 'edit')
  })

  /**
   * 检查是否有删除权限
   */
  const canDelete = computed(() => {
    return (resource: ResourceCode): boolean => hasPermission.value(resource, 'delete')
  })

  /**
   * 是否为校区管理员
   */
  const isCampusAdmin = computed(() => roleCode.value === 'campus_admin')

  /**
   * 是否为教师角色
   */
  const isTeacher = computed(() => roleCode.value === 'teacher')

  /**
   * 是否为学生角色
   */
  const isStudent = computed(() => roleCode.value === 'student')

  /**
   * 用户是否有校区限制
   */
  const hasCampusRestriction = computed(() => campusId.value !== null && !isSuperAdmin.value)

  // Actions
  /**
   * 从后端加载当前用户权限
   */
  async function loadPermissions(): Promise<void> {
    try {
      const info: UserPermissionInfo = await permissionApi.getCurrentUserPermissions()

      // 更新状态
      roleCode.value = info.role_code
      roleName.value = info.role_name
      campusId.value = info.campus_id
      campusName.value = info.campus_name
      isSuperAdmin.value = info.is_super_admin

      // 转换权限列表为Set
      permissions.value = new Set(info.permissions)
      isLoaded.value = true

      console.log('[PermissionStore] Loaded permissions:', {
        roleCode: roleCode.value,
        isSuperAdmin: isSuperAdmin.value,
        campusId: campusId.value,
        permissionCount: permissions.value.size
      })
    } catch (error) {
      console.error('[PermissionStore] Failed to load permissions:', error)
      clearPermissions()
      throw error
    }
  }

  /**
   * 清空权限状态（登出时调用）
   */
  function clearPermissions(): void {
    permissions.value = new Set()
    roleCode.value = null
    roleName.value = null
    campusId.value = null
    campusName.value = null
    isSuperAdmin.value = false
    isLoaded.value = false
  }

  /**
   * 批量检查多个权限（至少需要一个权限）
   */
  function hasAnyPermission(checks: Array<{ resource: ResourceCode; action: PermissionAction }>): boolean {
    if (isSuperAdmin.value) return true
    return checks.some(({ resource, action }) => permissions.value.has(`${resource}:${action}`))
  }

  /**
   * 批量检查多个权限（需要全部权限）
   */
  function hasAllPermissions(checks: Array<{ resource: ResourceCode; action: PermissionAction }>): boolean {
    if (isSuperAdmin.value) return true
    return checks.every(({ resource, action }) => permissions.value.has(`${resource}:${action}`))
  }

  /**
   * 获取用户可访问的菜单资源列表
   */
  function getAccessibleResources(): ResourceCode[] {
    if (isSuperAdmin.value) {
      // 超级管理员返回所有资源
      return [
        'dashboard', 'student', 'teacher', 'course', 'class_plan',
        'enrollment', 'schedule', 'campus', 'classroom', 'user',
        'dictionary', 'role_permission', 'system'
      ]
    }

    // 根据权限过滤资源
    const resources: ResourceCode[] = []
    const allResources: ResourceCode[] = [
      'dashboard', 'student', 'teacher', 'course', 'class_plan',
      'enrollment', 'schedule', 'campus', 'classroom', 'user',
      'dictionary', 'role_permission', 'system'
    ]

    for (const resource of allResources) {
      if (permissions.value.has(`${resource}:read`)) {
        resources.push(resource)
      }
    }

    return resources
  }

  return {
    // State
    permissions,
    roleCode,
    roleName,
    campusId,
    campusName,
    isSuperAdmin,
    isLoaded,
    // Getters
    hasPermission,
    canRead,
    canEdit,
    canDelete,
    isCampusAdmin,
    isTeacher,
    isStudent,
    hasCampusRestriction,
    // Actions
    loadPermissions,
    clearPermissions,
    hasAnyPermission,
    hasAllPermissions,
    getAccessibleResources
  }
})
