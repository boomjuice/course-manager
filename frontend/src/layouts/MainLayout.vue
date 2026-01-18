<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { usePermissionStore } from '@/stores/permission'
import { getAllCampuses, type Campus } from '@/api/campus'
import type { ResourceCode } from '@/types/permission'
import {
  HomeFilled,
  Calendar,
  User,
  UserFilled,
  Reading,
  School,
  Document,
  Setting,
  OfficeBuilding,
  List,
  ArrowDown,
  Key,
  Loading
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const permissionStore = usePermissionStore()

const isCollapse = ref(false)
const currentUser = computed(() => authStore.currentUser)

// Campus related state
const allCampuses = ref<Campus[]>([])
const showCampusSwitcher = ref(false)
const switchingCampus = ref(false)

// Get current campus name
const currentCampusName = computed(() => {
  if (!authStore.currentCampusId) return null
  const campus = allCampuses.value.find(c => c.id === authStore.currentCampusId)
  return campus?.name || null
})

// Check if user can switch campus (super_admin or teacher with multiple campuses)
const canSwitchCampus = computed(() => {
  const roleCode = permissionStore.roleCode
  return roleCode === 'super_admin' || roleCode === 'teacher'
})

// Menu item definition with required permission
interface MenuItem {
  path: string
  title: string
  icon: any
  resource: ResourceCode  // Required permission resource
}

// 业务模块菜单（侧边栏）
const businessMenuItems: MenuItem[] = [
  { path: '/dashboard', title: '仪表盘', icon: HomeFilled, resource: 'dashboard' },
  { path: '/schedule', title: '课表管理', icon: Calendar, resource: 'schedule' },
  { path: '/students', title: '学生管理', icon: User, resource: 'student' },
  { path: '/teachers', title: '教师管理', icon: UserFilled, resource: 'teacher' },
  { path: '/course-products', title: '课程产品', icon: Reading, resource: 'course' },
  { path: '/course-offerings', title: '开班计划', icon: Document, resource: 'class_plan' },
  { path: '/enrollments', title: '报名管理', icon: List, resource: 'enrollment' },
  { path: '/classrooms', title: '教室管理', icon: School, resource: 'classroom' },
]

// 系统管理菜单（右上角齿轮下拉）
const systemMenuItems: MenuItem[] = [
  { path: '/campuses', title: '校区管理', icon: OfficeBuilding, resource: 'campus' },
  { path: '/users', title: '用户管理', icon: UserFilled, resource: 'user' },
  { path: '/settings/data-dictionary', title: '数据字典', icon: Setting, resource: 'dictionary' },
  { path: '/settings/roles', title: '角色权限', icon: Key, resource: 'role_permission' },
  { path: '/settings/system', title: '系统设置', icon: Setting, resource: 'system' },
]

// Filter menu items based on user permissions
const menuItems = computed(() => {
  // 权限未加载时，返回所有菜单项作为占位（避免 el-menu 空数组报错）
  if (!permissionStore.isLoaded) {
    return businessMenuItems
  }
  return businessMenuItems.filter(item => {
    return permissionStore.canRead(item.resource)
  })
})

// 系统管理菜单（过滤权限）
const systemItems = computed(() => {
  if (!permissionStore.isLoaded) {
    return []
  }
  return systemMenuItems.filter(item => {
    return permissionStore.canRead(item.resource)
  })
})

// 是否显示系统管理入口
const showSystemMenu = computed(() => systemItems.value.length > 0)

// 系统管理菜单点击
const handleSystemCommand = (path: string) => {
  router.push(path)
}

const handleLogout = async () => {
  await authStore.logout()
  router.push({ name: 'Login' })
}

const handleCommand = (command: string) => {
  if (command === 'profile') {
    router.push({ name: 'Profile' })
  } else if (command === 'logout') {
    handleLogout()
  }
}

// Load all campuses for switcher
const loadCampuses = async () => {
  try {
    const response = await getAllCampuses(true)
    allCampuses.value = response || []
  } catch (error) {
    console.error('Failed to load campuses:', error)
  }
}

// Handle campus switch
const handleSwitchCampus = async (campusId: number) => {
  if (campusId === authStore.currentCampusId) {
    showCampusSwitcher.value = false
    return
  }

  switchingCampus.value = true
  try {
    await authStore.selectCampus(campusId)
    showCampusSwitcher.value = false
    ElMessage.success('校区切换成功')
    // Reload current page to refresh data
    router.go(0)
  } catch (error: any) {
    console.error('Failed to switch campus:', error)
  } finally {
    switchingCampus.value = false
  }
}

onMounted(() => {
  if (canSwitchCampus.value) {
    loadCampuses()
  }
})

// Reload campuses when permission changes
watch(() => permissionStore.roleCode, () => {
  if (canSwitchCampus.value) {
    loadCampuses()
  }
})
</script>

<template>
  <el-container class="layout-container">
    <!-- Sidebar -->
    <el-aside :width="isCollapse ? '64px' : '240px'" class="sidebar">
      <div class="logo">
        <span v-if="!isCollapse">课程管理系统</span>
        <span v-else>课</span>
      </div>

      <el-menu
        :default-active="route.path"
        :collapse="isCollapse"
        router
        class="sidebar-menu"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="item.path"
          :class="{ 'menu-item-disabled': !permissionStore.isLoaded }"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- Main Content -->
    <el-container>
      <!-- Header -->
      <el-header class="header">
        <div class="header-left">
          <el-button
            :icon="isCollapse ? 'Expand' : 'Fold'"
            text
            @click="isCollapse = !isCollapse"
          />
        </div>

        <div class="header-right">
          <!-- Campus Switcher -->
          <el-popover
            v-if="canSwitchCampus"
            v-model:visible="showCampusSwitcher"
            placement="bottom"
            :width="240"
            trigger="click"
          >
            <template #reference>
              <div class="campus-switcher">
                <el-icon><OfficeBuilding /></el-icon>
                <span>{{ currentCampusName || '选择校区' }}</span>
                <el-icon class="arrow"><ArrowDown /></el-icon>
              </div>
            </template>
            <div class="campus-popover">
              <div class="campus-popover-title">切换校区</div>
              <div class="campus-popover-list">
                <div
                  v-for="campus in allCampuses"
                  :key="campus.id"
                  class="campus-popover-item"
                  :class="{ active: campus.id === authStore.currentCampusId }"
                  @click="handleSwitchCampus(campus.id)"
                >
                  <el-icon><OfficeBuilding /></el-icon>
                  <span>{{ campus.name }}</span>
                  <el-icon v-if="campus.id === authStore.currentCampusId" class="check">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                    </svg>
                  </el-icon>
                </div>
              </div>
              <div v-if="switchingCampus" class="campus-popover-loading">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>切换中...</span>
              </div>
            </div>
          </el-popover>

          <!-- Fixed campus display (for campus_admin/student) -->
          <div v-else-if="currentCampusName" class="campus-display">
            <el-icon><OfficeBuilding /></el-icon>
            <span>{{ currentCampusName }}</span>
          </div>

          <!-- System Settings Dropdown -->
          <el-dropdown v-if="showSystemMenu" @command="handleSystemCommand" trigger="click">
            <span class="system-settings-trigger">
              <el-icon :size="18"><Setting /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  v-for="item in systemItems"
                  :key="item.path"
                  :command="item.path"
                >
                  <el-icon><component :is="item.icon" /></el-icon>
                  <span>{{ item.title }}</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <!-- User Dropdown -->
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :src="currentUser?.avatar">
                {{ currentUser?.username?.charAt(0).toUpperCase() }}
              </el-avatar>
              <span class="username">{{ currentUser?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人设置</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- Main Content Area -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped lang="scss">
.layout-container {
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  background: var(--bg-primary);
  border-right: 1px solid var(--border-light);
  transition: width var(--transition-normal);
  overflow: hidden;

  .logo {
    height: var(--header-height);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: 600;
    color: var(--primary-600);
    border-bottom: 1px solid var(--border-light);
    white-space: nowrap;
    overflow: hidden;
  }

  .sidebar-menu {
    border-right: none;
    padding: var(--spacing-sm);
  }

  .menu-item-disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.header {
  height: var(--header-height);
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-lg);

  .header-left {
    display: flex;
    align-items: center;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }

  .campus-switcher,
  .campus-display {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-md);
    border-radius: var(--radius-md);
    font-size: 14px;
    color: var(--text-secondary);
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    transition: all var(--transition-fast);

    .el-icon {
      font-size: 16px;
    }

    .arrow {
      font-size: 12px;
      margin-left: 4px;
    }
  }

  .campus-switcher {
    cursor: pointer;

    &:hover {
      border-color: var(--primary-300);
      color: var(--primary-500);
    }
  }

  .system-settings-trigger {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: var(--radius-md);
    cursor: pointer;
    color: var(--text-secondary);
    transition: all var(--transition-fast);

    &:hover {
      background: var(--bg-secondary);
      color: var(--primary-500);
    }
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    cursor: pointer;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-md);
    transition: background var(--transition-fast);

    &:hover {
      background: var(--bg-secondary);
    }

    .username {
      font-weight: 500;
      color: var(--text-primary);
    }
  }
}

// Campus Popover Styles
.campus-popover {
  .campus-popover-title {
    font-size: 12px;
    color: var(--text-tertiary);
    padding-bottom: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
    border-bottom: 1px solid var(--border-light);
  }

  .campus-popover-list {
    max-height: 240px;
    overflow-y: auto;
  }

  .campus-popover-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: background var(--transition-fast);

    &:hover {
      background: var(--bg-secondary);
    }

    &.active {
      background: var(--primary-50);
      color: var(--primary-600);
    }

    .el-icon:first-child {
      font-size: 16px;
      color: var(--text-tertiary);
    }

    span {
      flex: 1;
      font-size: 14px;
    }

    .check {
      color: var(--primary-500);
      font-size: 16px;
    }
  }

  .campus-popover-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
    color: var(--text-secondary);
    font-size: 13px;
  }
}

.main-content {
  background: var(--bg-secondary);
  overflow-y: auto;
  padding: var(--spacing-lg);
}
</style>
