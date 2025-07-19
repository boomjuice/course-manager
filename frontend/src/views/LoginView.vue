<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <span>欢迎登录 - 排课管理系统</span>
        </div>
      </template>
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-width="80px"
        @keyup.enter="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="loginForm.username" placeholder="请输入用户名"></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
          ></el-input>
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            @click="handleLogin" 
            class="login-button"
            :loading="loading"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import apiClient from '@/api'
import { useUserStore } from '@/stores/user'

const loginFormRef = ref<FormInstance>()
const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

const loginForm = reactive({
  username: 'admin', // 默认填入用于测试
  password: 'password', // 默认填入用于测试
})

const loginRules = reactive<FormRules>({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
})

const handleLogin = async () => {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const response = await apiClient.post('/auth/login/', {
          username: loginForm.username,
          password: loginForm.password,
        })
        
        if (response.data.token) {
          userStore.setToken(response.data.token)
          userStore.setUsername(loginForm.username)
          userStore.isAuthenticated = true
          
          ElMessage.success('登录成功！')
          await router.push('/schedule')
        }
      } catch (error) {
        // 错误消息已由 apiClient 的响应拦截器处理
        console.error('Login failed:', error)
      } finally {
        loading.value = false
      }
    } else {
      ElMessage.error('请填写完整的登录信息')
      return false
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}
.login-card {
  width: 450px;
}
.card-header {
  text-align: center;
  font-size: 20px;
  font-weight: bold;
}
.login-button {
  width: 100%;
}
</style>
