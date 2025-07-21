<template>
  <el-container class="main-layout">
    <el-aside width="200px">
      <Logo />
      <el-menu
        :default-active="activeMenu"
        active-text-color="#409EFF"
        background-color="#ffffff"
        class="el-menu-vertical-demo"
        text-color="#303133"
        router
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/schedule">
          <el-icon><icon-menu /></el-icon>
          <span>课表管理</span>
        </el-menu-item>

        <el-sub-menu index="academic">
          <template #title>
            <el-icon><document /></el-icon>
            <span>教务管理</span>
          </template>
          <el-menu-item index="/course-offerings">开班计划</el-menu-item>
          <el-menu-item index="/enrollments">报名管理</el-menu-item>
          <el-menu-item index="/products">课程产品</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="personnel">
          <template #title>
            <el-icon><user /></el-icon>
            <span>人员管理</span>
          </template>
          <el-menu-item index="/students">学生管理</el-menu-item>
          <el-menu-item index="/teachers">教师管理</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="settings">
          <template #title>
            <el-icon><setting /></el-icon>
            <span>系统设置</span>
          </template>
          <el-menu-item index="/settings/data-dictionary">数据字典</el-menu-item>
          <el-menu-item index="/settings/classrooms">教室管理</el-menu-item>
          <el-menu-item index="/settings/campuses">校区管理</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="main-header">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="{ path: item.path }">
            {{ item.meta.title }}
          </el-breadcrumb-item>
        </el-breadcrumb>
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
import { computed } from 'vue';
import {
  Document,
  Menu as IconMenu,
  Setting,
  ArrowDown,
  User,
  HomeFilled
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useRouter, useRoute } from 'vue-router'
import Logo from './Logo.vue';

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => {
  const { path } = route;
  return path;
});

const breadcrumbs = computed(() => {
  return route.matched.filter(item => item.meta && item.meta.title);
});

const handleCommand = (command: string | number | object) => {
  if (command === 'logout') {
    userStore.clearAuth()
    router.push('/login')
  }
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}
.el-menu-vertical-demo {
  height: calc(100vh - 60px); /* Adjust for logo height */
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
