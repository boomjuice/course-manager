<template>
  <div class="profile-settings-view">
    <div class="page-header">
      <h1>个人设置</h1>
    </div>

    <el-row :gutter="20">
      <!-- Profile Info Card -->
      <el-col :span="12">
        <el-card class="profile-card">
          <template #header>
            <div class="card-header">
              <span>个人信息</span>
            </div>
          </template>

          <el-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="profileRules"
            label-width="80px"
          >
            <el-form-item label="用户名">
              <el-input :value="user?.username" disabled />
            </el-form-item>
            <el-form-item label="角色">
              <el-tag :type="getRoleType(user?.role)">
                {{ getRoleLabel(user?.role) }}
              </el-tag>
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="手机" prop="phone">
              <el-input v-model="profileForm.phone" placeholder="请输入手机号" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSaveProfile" :loading="savingProfile">
                保存
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- Password Change Card -->
      <el-col :span="12">
        <el-card class="password-card">
          <template #header>
            <div class="card-header">
              <span>修改密码</span>
            </div>
          </template>

          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="100px"
          >
            <el-form-item label="当前密码" prop="oldPassword">
              <el-input
                v-model="passwordForm.oldPassword"
                type="password"
                show-password
                placeholder="请输入当前密码"
              />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input
                v-model="passwordForm.newPassword"
                type="password"
                show-password
                placeholder="请输入新密码"
              />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input
                v-model="passwordForm.confirmPassword"
                type="password"
                show-password
                placeholder="请再次输入新密码"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleChangePassword" :loading="changingPassword">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- Account Info -->
    <el-card class="account-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>账号信息</span>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="账号状态">
          <el-tag :type="user?.is_active ? 'success' : 'danger'">
            {{ user?.is_active ? '正常' : '已禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="在线状态">
          <el-tag :type="user?.is_online ? 'success' : 'info'">
            {{ user?.is_online ? '在线' : '离线' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="最后登录">
          {{ formatDateTime(user?.last_login) }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(user?.created_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDateTime(user?.updated_time) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const user = computed(() => authStore.currentUser)

// Profile Form
const profileFormRef = ref<FormInstance>()
const savingProfile = ref(false)
const profileForm = ref({
  email: '',
  phone: '',
})

const profileRules: FormRules = {
  email: [
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
}

// Password Form
const passwordFormRef = ref<FormInstance>()
const changingPassword = ref(false)
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const passwordRules: FormRules = {
  oldPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' },
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== passwordForm.value.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// Methods
const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getRoleLabel = (role?: string) => {
  const map: Record<string, string> = { admin: '管理员', teacher: '教师', student: '学生' }
  return map[role || ''] || role || '-'
}

const getRoleType = (role?: string) => {
  const map: Record<string, string> = { admin: 'danger', teacher: 'warning', student: 'info' }
  return map[role || ''] || 'info'
}

const handleSaveProfile = async () => {
  await profileFormRef.value?.validate()
  savingProfile.value = true
  try {
    await authStore.updateProfile({
      email: profileForm.value.email || undefined,
      phone: profileForm.value.phone || undefined,
    })
    ElMessage.success('保存成功')
  } finally {
    savingProfile.value = false
  }
}

const handleChangePassword = async () => {
  await passwordFormRef.value?.validate()
  changingPassword.value = true
  try {
    await authStore.changePassword(
      passwordForm.value.oldPassword,
      passwordForm.value.newPassword
    )
    ElMessage.success('密码修改成功')
    // Clear form
    passwordForm.value = {
      oldPassword: '',
      newPassword: '',
      confirmPassword: '',
    }
  } finally {
    changingPassword.value = false
  }
}

onMounted(() => {
  // Initialize form with current user data
  if (user.value) {
    profileForm.value.email = user.value.email || ''
    profileForm.value.phone = user.value.phone || ''
  }
})
</script>

<style scoped lang="scss">
.profile-settings-view {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;

  h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
  }
}

.card-header {
  display: flex;
  align-items: center;
  font-weight: 600;
}

.profile-card,
.password-card,
.account-card {
  :deep(.el-card__header) {
    padding: 12px 20px;
    background-color: var(--el-fill-color-light);
  }
}
</style>
