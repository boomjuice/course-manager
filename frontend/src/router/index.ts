/**
 * Vue Router Configuration
 */
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw, RouteMeta } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePermissionStore } from '@/stores/permission'
import type { ResourceCode, PermissionAction } from '@/types/permission'

// Extended route meta type
interface ExtendedRouteMeta extends RouteMeta {
  title?: string
  requiresAuth?: boolean
  // RBAC permission requirement: [resource, action]
  permission?: [ResourceCode, PermissionAction]
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login/LoginView.vue'),
    meta: { requiresAuth: false, title: '登录' }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard/DashboardView.vue'),
        meta: { title: '仪表盘', permission: ['dashboard', 'read'] } as ExtendedRouteMeta
      },
      {
        path: 'schedule',
        name: 'Schedule',
        component: () => import('@/views/Schedule/ScheduleView.vue'),
        meta: { title: '课表管理', permission: ['schedule', 'read'] } as ExtendedRouteMeta
      },
      {
        path: 'students',
        name: 'Students',
        component: () => import('@/views/Student/StudentListView.vue'),
        meta: { title: '学生管理', permission: ['student', 'read'] } as ExtendedRouteMeta
      },
      {
        path: 'teachers',
        name: 'Teachers',
        component: () => import('@/views/Teacher/TeacherListView.vue'),
        meta: { title: '教师管理', permission: ['teacher', 'read'] } as ExtendedRouteMeta
      },
      {
        path: 'course-products',
        name: 'CourseProducts',
        component: () => import('@/views/Course/CourseProductListView.vue'),
        meta: { title: '课程产品', permission: ['course', 'read'] } as ExtendedRouteMeta
      },
      {
        path: 'course-offerings',
        name: 'CourseOfferings',
        component: () => import('@/views/Course/CourseOfferingListView.vue'),
        meta: { title: '开班计划', permission: ['class_plan', 'read'] } as ExtendedRouteMeta
      },
      {
        path: 'enrollments',
        name: 'Enrollments',
        component: () => import('@/views/Enrollment/EnrollmentListView.vue'),
        meta: { title: '报名管理', permission: ['enrollment', 'read'] } as ExtendedRouteMeta
      },
      {
        path: 'campuses',
        name: 'Campuses',
        component: () => import('@/views/Campus/CampusListView.vue'),
        meta: { title: '校区管理', permission: ['campus', 'read'] } as ExtendedRouteMeta
      },
      {
        path: 'classrooms',
        name: 'Classrooms',
        component: () => import('@/views/Campus/ClassroomListView.vue'),
        meta: { title: '教室管理', permission: ['classroom', 'read'] } as ExtendedRouteMeta
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/User/UserListView.vue'),
        meta: { title: '用户管理', permission: ['user', 'read'] } as ExtendedRouteMeta
      },
      {
        path: 'login-logs',
        name: 'LoginLogs',
        component: () => import('@/views/User/LoginLogListView.vue'),
        meta: { title: '登录日志', permission: ['user', 'read'] } as ExtendedRouteMeta
      },
      {
        path: 'settings/data-dictionary',
        name: 'DataDictionary',
        component: () => import('@/views/Settings/Dictionary/DictionaryView.vue'),
        meta: { title: '数据字典', permission: ['dictionary', 'read'] } as ExtendedRouteMeta
      },
      {
        path: 'settings/profile',
        name: 'Profile',
        component: () => import('@/views/Settings/ProfileSettingsView.vue'),
        meta: { title: '个人设置' }  // No permission needed - everyone can access their own profile
      },
      {
        path: 'settings/system',
        name: 'SystemSettings',
        component: () => import('@/views/Settings/SystemSettingsView.vue'),
        meta: { title: '系统管理', permission: ['system', 'read'] } as ExtendedRouteMeta
      },
      {
        path: 'settings/roles',
        name: 'RoleManagement',
        component: () => import('@/views/Settings/RoleManagementView.vue'),
        meta: { title: '角色权限', permission: ['role_permission', 'read'] } as ExtendedRouteMeta
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard with RBAC permission check
router.beforeEach(async (to, _from, next) => {
  // Set page title
  document.title = `${to.meta.title || '课程管理系统'} - 课程管理系统`

  const authStore = useAuthStore()
  const permissionStore = usePermissionStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)

  // Check authentication
  if (requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // Redirect to dashboard if already logged in and trying to access login page
  if (to.name === 'Login' && authStore.isAuthenticated) {
    next({ name: 'Dashboard' })
    return
  }

  // Load permissions if not loaded yet (for authenticated users)
  if (authStore.isAuthenticated && !permissionStore.isLoaded) {
    try {
      await permissionStore.loadPermissions()
    } catch (error) {
      console.error('Failed to load permissions in route guard:', error)
      // Clear auth and redirect to login if permission loading fails
      authStore.clearAuth()
      next({ name: 'Login' })
      return
    }
  }

  // Check RBAC permission
  const permission = to.meta.permission as [ResourceCode, PermissionAction] | undefined
  if (permission && authStore.isAuthenticated) {
    const [resource, action] = permission
    const hasPermission = permissionStore.hasPermission(resource, action)

    if (!hasPermission) {
      console.warn(`[Router] Permission denied: ${resource}:${action}`)
      // Redirect to dashboard if no permission
      next({ name: 'Dashboard' })
      return
    }
  }

  next()
})

export default router
