import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'
import LoginView from '@/views/LoginView.vue'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: MainLayout,
      meta: { requiresAuth: true, title: '首页' },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
          meta: { title: '仪表盘' }
        },
        {
          path: 'schedule',
          name: 'schedule',
          component: () => import('@/views/ScheduleView.vue'),
          meta: { title: '课表管理' }
        },
        {
          path: 'course-offerings',
          name: 'course-offerings',
          component: () => import('@/views/CourseOfferingListView.vue'),
          meta: { title: '开班计划' }
        },
        {
          path: 'enrollments',
          name: 'enrollments',
          component: () => import('@/views/EnrollmentListView.vue'),
          meta: { title: '报名管理' }
        },
        {
          path: 'products',
          name: 'products',
          component: () => import('@/views/CourseProductListView.vue'),
          meta: { title: '课程产品' }
        },
        {
          path: 'students',
          name: 'students',
          component: () => import('@/views/StudentListView.vue'),
          meta: { title: '学生管理' }
        },
        {
          path: 'teachers',
          name: 'teachers',
          component: () => import('@/views/TeacherListView.vue'),
          meta: { title: '教师管理' }
        },
        {
          path: 'settings',
          name: 'settings',
          component: { template: '<router-view />' }, // Parent for settings
          meta: { title: '系统设置' },
          children: [
            {
              path: 'classrooms',
              name: 'classrooms',
              component: () => import('@/views/ClassroomListView.vue'),
              meta: { title: '教室管理' }
            },
            {
              path: 'campuses',
              name: 'campuses',
              component: () => import('@/views/CampusListView.vue'),
              meta: { title: '校区管理' }
            },
            {
              path: 'data-dictionary',
              name: 'data-dictionary',
              component: () => import('@/views/DataDictionaryListView.vue'),
              meta: { title: '数据字典' }
            },
          ]
        }
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    next({ name: 'login' })
  } else if (to.name === 'login' && userStore.isAuthenticated) {
    next({ path: '/' })
  }
  else {
    next()
  }
})

export default router
