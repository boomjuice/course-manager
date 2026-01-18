<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import type { FormInstance, FormRules } from 'element-plus'
import { User, Lock, OfficeBuilding } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const selectingCampus = ref(false)
const selectedCampusId = ref<number | null>(null)

const form = reactive({
  username: '',
  password: ''
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

// Show campus selection after login if needed
const showCampusSelection = computed(() => authStore.needSelectCampus && selectingCampus.value)

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const response = await authStore.login({
        username: form.username,
        password: form.password
      })

      if (response.need_select_campus) {
        // Show campus selection
        selectingCampus.value = true
        ElMessage.info('请选择要进入的校区')
      } else {
        ElMessage.success('登录成功')
        // Redirect to original page or dashboard
        const redirect = route.query.redirect as string
        router.push(redirect || '/dashboard')
      }
    } catch (error: any) {
      // Error is handled by axios interceptor
      console.error('Login failed:', error)
    } finally {
      loading.value = false
    }
  })
}

const handleSelectCampus = async () => {
  if (!selectedCampusId.value) {
    ElMessage.warning('请选择一个校区')
    return
  }

  loading.value = true
  try {
    await authStore.selectCampus(selectedCampusId.value)
    ElMessage.success('登录成功')

    // Redirect to original page or dashboard
    const redirect = route.query.redirect as string
    router.push(redirect || '/dashboard')
  } catch (error: any) {
    console.error('Campus selection failed:', error)
  } finally {
    loading.value = false
  }
}

const handleBackToLogin = () => {
  selectingCampus.value = false
  authStore.clearAuth()
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>课程管理系统</h1>
        <p>教育培训管理平台</p>
      </div>

      <!-- Login Form -->
      <el-form
        v-if="!showCampusSelection"
        ref="formRef"
        :model="form"
        :rules="rules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <!-- Campus Selection -->
      <div v-else class="campus-selection">
        <div class="campus-selection-header">
          <el-icon :size="32" color="var(--primary-500)"><OfficeBuilding /></el-icon>
          <h3>选择校区</h3>
          <p>请选择要进入的校区</p>
        </div>

        <div class="campus-list">
          <div
            v-for="campus in authStore.availableCampuses"
            :key="campus.id"
            class="campus-item"
            :class="{ selected: selectedCampusId === campus.id }"
            @click="selectedCampusId = campus.id"
          >
            <el-icon><OfficeBuilding /></el-icon>
            <span>{{ campus.name }}</span>
            <el-icon v-if="selectedCampusId === campus.id" class="check-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
              </svg>
            </el-icon>
          </div>
        </div>

        <div class="campus-actions">
          <el-button size="large" @click="handleBackToLogin">
            返回登录
          </el-button>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            :disabled="!selectedCampusId"
            @click="handleSelectCampus"
          >
            进入系统
          </el-button>
        </div>
      </div>

      <div class="login-footer">
        <p>课程管理系统 V2.0</p>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-50) 0%, var(--primary-100) 100%);
}

.login-card {
  width: 400px;
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: var(--spacing-2xl);
}

.login-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);

  h1 {
    font-size: 28px;
    font-weight: 600;
    color: var(--primary-600);
    margin-bottom: var(--spacing-sm);
  }

  p {
    color: var(--text-tertiary);
    font-size: 14px;
  }
}

.login-form {
  .el-form-item {
    margin-bottom: var(--spacing-lg);
  }

  .el-input {
    --el-input-height: 48px;
  }
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
}

.login-footer {
  text-align: center;
  margin-top: var(--spacing-xl);

  p {
    color: var(--text-tertiary);
    font-size: 12px;
  }
}

// Campus Selection Styles
.campus-selection {
  .campus-selection-header {
    text-align: center;
    margin-bottom: var(--spacing-lg);

    .el-icon {
      margin-bottom: var(--spacing-sm);
    }

    h3 {
      font-size: 20px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: var(--spacing-xs);
    }

    p {
      color: var(--text-secondary);
      font-size: 14px;
    }
  }

  .campus-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-lg);
    max-height: 300px;
    overflow-y: auto;
  }

  .campus-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md) var(--spacing-lg);
    border: 2px solid var(--border-light);
    border-radius: var(--radius-lg);
    cursor: pointer;
    transition: all var(--transition-fast);

    &:hover {
      border-color: var(--primary-300);
      background: var(--primary-50);
    }

    &.selected {
      border-color: var(--primary-500);
      background: var(--primary-50);

      .el-icon:first-child {
        color: var(--primary-500);
      }
    }

    .el-icon:first-child {
      color: var(--text-tertiary);
      font-size: 20px;
    }

    span {
      flex: 1;
      font-size: 15px;
      font-weight: 500;
      color: var(--text-primary);
    }

    .check-icon {
      color: var(--primary-500);
      font-size: 20px;
    }
  }

  .campus-actions {
    display: flex;
    gap: var(--spacing-md);

    .el-button {
      flex: 1;
      height: 44px;
    }
  }
}
</style>
