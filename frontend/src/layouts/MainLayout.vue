<template>
  <el-container class="main-layout">
    <el-aside width="200px">
      <el-menu
        active-text-color="#409EFF"
        background-color="#ffffff"
        class="el-menu-vertical-demo"
        default-active="/schedule"
        text-color="#303133"
        router
      >
        <el-menu-item index="/schedule">
          <el-icon><icon-menu /></el-icon>
          <span>课表管理</span>
        </el-menu-item>
        <el-menu-item index="/classes">
          <el-icon><document /></el-icon>
          <span>班级管理</span>
        </el-menu-item>
        <el-menu-item index="/students">
          <el-icon><setting /></el-icon>
          <span>学生管理</span>
        </el-menu-item>
         <el-menu-item index="/teachers">
          <el-icon><setting /></el-icon>
          <span>教师管理</span>
        </el-menu-item>
        <el-sub-menu index="settings">
          <template #title>
            <el-icon><setting /></el-icon>
            <span>系统设置</span>
          </template>
          <el-menu-item index="/settings/grades">年级管理</el-menu-item>
          <el-menu-item index="/settings/subjects">科目管理</el-menu-item>
          <el-menu-item index="/settings/tags">标签管理</el-menu-item>
          <el-menu-item index="/settings/classrooms">教室管理</el-menu-item>
          <el-menu-item index="/settings/campuses">校区管理</el-menu-item>
          <el-menu-item index="/settings/timeslots">时间段管理</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="main-header">
        <div>面包屑 / 导航</div>
        <div class="user-info">
          <el-dropdown @command="handleCommand">
            <span class="el-dropdown-link">
              欢迎, {{ userStore.username }}
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script lang="ts" setup>
import {
  Document,
  Menu as IconMenu,
  Setting,
  ArrowDown
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

const handleCommand = (command: string | number | object) => {
  if (command === 'logout') {
    userStore.clearAuth()
    router.push('/login')
  }
}
</script>

<style scoped>
.main-layout, .el-menu-vertical-demo {
  height: 100vh;
}
.el-aside {
  border-right: 1px solid #ebeef5;
}
.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fcfcfc;
  border-bottom: 1px solid #ebeef5;
}
.user-info {
  cursor: pointer;
}
</style>
