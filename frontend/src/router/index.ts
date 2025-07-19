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
      meta: { requiresAuth: true },
      children: [
        {
          path: '/schedule',
          name: 'schedule',
          component: () => import('@/views/ScheduleView.vue')
        },
        {
          path: '/classes',
          name: 'classes',
          component: () => import('@/views/ClassListView.vue')
        },
        {
          path: '/students',
          name: 'students',
          component: () => import('@/views/StudentListView.vue')
        },
        {
          path: '/teachers',
          name: 'teachers',
          component: () => import('@/views/TeacherListView.vue')
        },
        {
          path: '/settings/grades',
          name: 'grades',
          component: () => import('@/views/GradeListView.vue')
        },
        {
          path: '/settings/subjects',
          name: 'subjects',
          component: () => import('@/views/SubjectListView.vue')
        },
        {
          path: '/settings/tags',
          name: 'tags',
          component: () => import('@/views/TagListView.vue')
        },
        {
          path: '/settings/classrooms',
          name: 'classrooms',
          component: () => import('@/views/ClassroomListView.vue')
        },
        {
          path: '/settings/campuses',
          name: 'campuses',
          component: () => import('@/views/CampusListView.vue')
        },
        {
          path: '/settings/timeslots',
          name: 'timeslots',
          component: () => import('@/views/TimeSlotListView.vue')
        }
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    // 此路由需要身份验证，请检查用户是否已登录
    // 如果没有，则重定向到登录页面
    next({ name: 'login' })
  } else if (to.name === 'login' && userStore.isAuthenticated) {
    // 如果用户已通过身份验证，则不允许他们访问登录页面
    next({ path: '/' })
  }
  else {
    // 确保一定要调用 next()
    next()
  }
})

export default router