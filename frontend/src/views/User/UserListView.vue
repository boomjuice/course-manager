<template>
  <div class="user-view">
    <div class="page-header">
      <h1>用户管理</h1>
      <el-button v-permission="['user', 'edit']" type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon>
        新增用户
      </el-button>
    </div>

    <!-- Search Bar -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索用户名/昵称..."
        clearable
        style="width: 220px"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="filterRoleId" placeholder="角色" clearable style="width: 140px">
        <el-option
          v-for="role in roles"
          :key="role.id"
          :label="role.name"
          :value="role.id"
        />
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 100px">
        <el-option label="启用" :value="true" />
        <el-option label="禁用" :value="false" />
      </el-select>
      <el-button @click="handleSearch">搜索</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- Table -->
    <el-table :data="users" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="username" label="用户名" width="150" />
      <el-table-column prop="nickname" label="昵称" width="120">
        <template #default="{ row }">
          {{ row.nickname || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="手机" width="130" />
      <el-table-column label="角色" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="getRoleType(row.role_code || row.role)">
            {{ row.role_name || getRoleLabel(row.role) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="所属校区" width="150">
        <template #default="{ row }">
          {{ row.campus_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="last_login" label="最后登录" width="170">
        <template #default="{ row }">
          {{ formatDate(row.last_login) }}
        </template>
      </el-table-column>
      <el-table-column prop="created_time" label="创建时间" width="170">
        <template #default="{ row }">
          {{ formatDate(row.created_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="300" fixed="right">
        <template #default="{ row }">
          <el-button v-permission="['user', 'edit']" link type="primary" @click="showDialog(row)">编辑</el-button>
          <el-button v-permission="['user', 'edit']" link type="warning" @click="showResetPwdDialog(row)">重置密码</el-button>
          <el-popconfirm title="确定删除该用户？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button v-permission="['user', 'delete']" link type="danger" :disabled="row.username === 'admin'">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadData"
        @current-change="loadData"
      />
    </div>

    <!-- User Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingItem ? '编辑用户' : '新增用户'"
      width="520px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!editingItem" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item v-if="!editingItem" label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" placeholder="请输入昵称" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="角色" prop="role_id">
          <el-select v-model="form.role_id" style="width: 100%" @change="handleRoleChange">
            <el-option
              v-for="role in roles"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <!-- 非超管角色需要选择校区 -->
        <el-form-item
          v-if="needSelectCampus"
          label="所属校区"
          prop="campus_id"
          :rules="[{ required: true, message: '请选择校区', trigger: 'change' }]"
        >
          <el-select v-model="form.campus_id" style="width: 100%" placeholder="请选择校区">
            <el-option
              v-for="campus in campuses"
              :key="campus.id"
              :label="campus.name"
              :value="campus.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- Reset Password Dialog -->
    <el-dialog v-model="resetPwdDialogVisible" title="重置密码" width="400px">
      <el-form ref="resetPwdFormRef" :model="resetPwdForm" :rules="resetPwdRules" label-width="80px">
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="resetPwdForm.newPassword" type="password" show-password placeholder="请输入新密码" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="resetPwdForm.confirmPassword" type="password" show-password placeholder="请再次输入密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPwdDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleResetPassword" :loading="resetPwdSaving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  getUsers, createUser, updateUser, deleteUser, resetUserPassword,
  type User, type UserCreate
} from '@/api/user'
import { permissionApi } from '@/api/permission'
import { getAllCampuses, type Campus } from '@/api/campus'
import type { Role } from '@/types/permission'

// State
const users = ref<User[]>([])
const roles = ref<Role[]>([])
const campuses = ref<Campus[]>([])
const loading = ref(false)
const saving = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const filterRoleId = ref<number | undefined>(undefined)
const filterStatus = ref<boolean | undefined>(undefined)

// Dialog
const dialogVisible = ref(false)
const editingItem = ref<User | null>(null)
const formRef = ref<FormInstance>()

interface UserForm {
  username: string
  password: string
  nickname: string
  email: string
  phone: string
  role_id: number | undefined
  campus_id: number | undefined
  is_active: boolean
}

const form = ref<UserForm>({
  username: '',
  password: '',
  nickname: '',
  email: '',
  phone: '',
  role_id: undefined,
  campus_id: undefined,
  is_active: true,
})

// 选择的角色编码
const selectedRoleCode = computed(() => {
  if (!form.value.role_id) return null
  const role = roles.value.find(r => r.id === form.value.role_id)
  return role?.code || null
})

// 是否需要选择校区
// 超管和教师不需要选校区（教师可跨校区上课，校区从班级计划来）
// 只有校区管理员和学生需要绑定校区
const needSelectCampus = computed(() => {
  const code = selectedRoleCode.value
  return code && code !== 'super_admin' && code !== 'teacher'
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role_id: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

// Reset Password Dialog
const resetPwdDialogVisible = ref(false)
const resetPwdSaving = ref(false)
const resetPwdUserId = ref(0)
const resetPwdFormRef = ref<FormInstance>()
const resetPwdForm = ref({ newPassword: '', confirmPassword: '' })
const resetPwdRules: FormRules = {
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== resetPwdForm.value.newPassword) {
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
const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getRoleLabel = (role: string) => {
  const map: Record<string, string> = {
    admin: '管理员',
    teacher: '教师',
    student: '学生',
    super_admin: '超级管理员',
    campus_admin: '校区管理员'
  }
  return map[role] || role
}

const getRoleType = (roleCode: string) => {
  const map: Record<string, string> = {
    super_admin: 'danger',
    admin: 'danger',
    campus_admin: 'warning',
    teacher: '',
    student: 'info'
  }
  return map[roleCode] || 'info'
}

// 加载角色列表
const loadRoles = async () => {
  try {
    const res = await permissionApi.getRoles({ is_active: true, page_size: 100 })
    roles.value = res.data?.items || []
  } catch (error) {
    console.error('Failed to load roles:', error)
  }
}

// 加载校区列表
const loadCampuses = async () => {
  try {
    const res = await getAllCampuses(true)
    campuses.value = res || []
  } catch (error) {
    console.error('Failed to load campuses:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getUsers({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchKeyword.value || undefined,
      role: filterRoleId.value ? undefined : undefined, // 暂时不支持role_id过滤
      is_active: filterStatus.value,
    })
    users.value = res.data?.items || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadData()
}

const handleReset = () => {
  searchKeyword.value = ''
  filterRoleId.value = undefined
  filterStatus.value = undefined
  currentPage.value = 1
  loadData()
}

const handleRoleChange = () => {
  // 切换角色时，如果是超管则清空校区
  if (selectedRoleCode.value === 'super_admin') {
    form.value.campus_id = undefined
  }
}

const showDialog = (item?: User) => {
  editingItem.value = item || null
  if (item) {
    form.value = {
      username: item.username,
      password: '',
      nickname: item.nickname || '',
      email: item.email || '',
      phone: item.phone || '',
      role_id: item.role_id,
      campus_id: item.campus_id,
      is_active: item.is_active,
    }
  } else {
    // 默认选择第一个非超管角色
    const defaultRole = roles.value.find(r => r.code === 'campus_admin') || roles.value[0]
    form.value = {
      username: '',
      password: '',
      nickname: '',
      email: '',
      phone: '',
      role_id: defaultRole?.id,
      campus_id: undefined,
      is_active: true,
    }
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  await formRef.value?.validate()

  // 非超管角色必须选择校区
  if (needSelectCampus.value && !form.value.campus_id) {
    ElMessage.warning('请选择所属校区')
    return
  }

  saving.value = true
  try {
    // 构建提交数据
    const selectedRole = roles.value.find(r => r.id === form.value.role_id)
    const submitData: UserCreate = {
      username: form.value.username,
      password: form.value.password,
      nickname: form.value.nickname || undefined,
      email: form.value.email || undefined,
      phone: form.value.phone || undefined,
      role_id: form.value.role_id,
      // 同时设置旧的role字段保持兼容
      role: selectedRole?.code === 'super_admin' || selectedRole?.code === 'campus_admin'
        ? 'admin'
        : selectedRole?.code || 'teacher',
      campus_id: needSelectCampus.value ? form.value.campus_id : undefined,
      is_active: form.value.is_active,
    }

    if (editingItem.value) {
      const { username, password, ...updateData } = submitData
      await updateUser(editingItem.value.id, updateData)
      ElMessage.success('更新成功')
    } else {
      await createUser(submitData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteUser(id)
  ElMessage.success('删除成功')
  loadData()
}

const showResetPwdDialog = (user: User) => {
  resetPwdUserId.value = user.id
  resetPwdForm.value = { newPassword: '', confirmPassword: '' }
  resetPwdDialogVisible.value = true
}

const handleResetPassword = async () => {
  await resetPwdFormRef.value?.validate()
  resetPwdSaving.value = true
  try {
    await resetUserPassword(resetPwdUserId.value, resetPwdForm.value.newPassword)
    ElMessage.success('密码重置成功')
    resetPwdDialogVisible.value = false
  } finally {
    resetPwdSaving.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadRoles(), loadCampuses()])
  loadData()
})
</script>

<style scoped lang="scss">
.user-view {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
  }
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
