<template>
  <div class="role-management">
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <span>角色权限管理</span>
          <el-button
            v-permission="['role_permission', 'edit']"
            type="primary"
            @click="showCreateDialog"
          >
            <el-icon><Plus /></el-icon>
            新建角色
          </el-button>
        </div>
      </template>

      <!-- 角色列表 -->
      <el-table :data="roles" v-loading="loading" stripe>
        <el-table-column prop="code" label="角色编码" width="150" />
        <el-table-column prop="name" label="角色名称" width="150" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column label="系统内置" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_system" type="warning" size="small">系统</el-tag>
            <el-tag v-else type="info" size="small">自定义</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_active" type="success" size="small">启用</el-tag>
            <el-tag v-else type="danger" size="small">禁用</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_time" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.created_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="center">
          <template #default="{ row }">
            <el-button
              v-permission="['role_permission', 'edit']"
              type="primary"
              size="small"
              @click="showPermissionDialog(row)"
            >
              配置权限
            </el-button>
            <el-button
              v-permission="['role_permission', 'edit']"
              size="small"
              @click="showEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button
              v-permission="['role_permission', 'delete']"
              type="danger"
              size="small"
              :disabled="row.is_system"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchRoles"
          @current-change="fetchRoles"
        />
      </div>
    </el-card>

    <!-- 创建/编辑角色对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      :title="isEditing ? '编辑角色' : '新建角色'"
      width="500px"
    >
      <el-form
        ref="roleFormRef"
        :model="roleForm"
        :rules="roleRules"
        label-width="80px"
      >
        <el-form-item label="角色编码" prop="code">
          <el-input
            v-model="roleForm.code"
            :disabled="isEditing"
            placeholder="请输入角色编码（英文）"
          />
        </el-form-item>
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="roleForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="roleForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入角色描述"
          />
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="roleForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitRole">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 权限配置对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      title="配置角色权限"
      width="800px"
    >
      <div v-if="selectedRole" class="permission-header">
        <span>角色：{{ selectedRole.name }}</span>
        <span class="role-code">({{ selectedRole.code }})</span>
      </div>

      <el-table
        :data="resources"
        v-loading="loadingPermissions"
        stripe
        border
      >
        <el-table-column prop="name" label="功能模块" width="150" />
        <el-table-column label="查看" width="100" align="center">
          <template #default="{ row }">
            <el-checkbox
              :model-value="hasPermission(row.code, 'read')"
              @change="(val: boolean) => togglePermission(row.code, 'read', val)"
            />
          </template>
        </el-table-column>
        <el-table-column label="编辑" width="100" align="center">
          <template #default="{ row }">
            <el-checkbox
              :model-value="hasPermission(row.code, 'edit')"
              @change="(val: boolean) => togglePermission(row.code, 'edit', val)"
            />
          </template>
        </el-table-column>
        <el-table-column label="删除" width="100" align="center">
          <template #default="{ row }">
            <el-checkbox
              :model-value="hasPermission(row.code, 'delete')"
              @change="(val: boolean) => togglePermission(row.code, 'delete', val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="200" />
      </el-table>

      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="savingPermissions"
          @click="savePermissions"
        >
          保存权限
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { permissionApi } from '@/api/permission'
import type {
  Role,
  RoleWithPermissions,
  ResourceWithPermissions,
  RoleCreate,
  RoleUpdate
} from '@/types/permission'

// State
const loading = ref(false)
const roles = ref<Role[]>([])
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// Role dialog state
const roleDialogVisible = ref(false)
const isEditing = ref(false)
const submitting = ref(false)
const roleFormRef = ref<FormInstance>()
const currentRoleId = ref<number | null>(null)
const roleForm = reactive<RoleCreate & { is_active: boolean }>({
  code: '',
  name: '',
  description: '',
  is_active: true
})

const roleRules: FormRules = {
  code: [
    { required: true, message: '请输入角色编码', trigger: 'blur' },
    { pattern: /^[a-z_]+$/, message: '只能包含小写字母和下划线', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' }
  ]
}

// Permission dialog state
const permissionDialogVisible = ref(false)
const loadingPermissions = ref(false)
const savingPermissions = ref(false)
const selectedRole = ref<RoleWithPermissions | null>(null)
const resources = ref<ResourceWithPermissions[]>([])
const selectedPermissionIds = ref<Set<number>>(new Set())

// Fetch roles
async function fetchRoles() {
  loading.value = true
  try {
    const response = await permissionApi.getRoles({
      page: pagination.page,
      page_size: pagination.pageSize
    })
    roles.value = response.data?.items || []
    pagination.total = response.data?.total || 0
  } catch (error) {
    console.error('Failed to fetch roles:', error)
  } finally {
    loading.value = false
  }
}

// Show create dialog
function showCreateDialog() {
  isEditing.value = false
  currentRoleId.value = null
  roleForm.code = ''
  roleForm.name = ''
  roleForm.description = ''
  roleForm.is_active = true
  roleDialogVisible.value = true
}

// Show edit dialog
function showEditDialog(role: Role) {
  isEditing.value = true
  currentRoleId.value = role.id
  roleForm.code = role.code
  roleForm.name = role.name
  roleForm.description = role.description || ''
  roleForm.is_active = role.is_active
  roleDialogVisible.value = true
}

// Submit role create/update
async function submitRole() {
  if (!roleFormRef.value) return

  try {
    await roleFormRef.value.validate()
    submitting.value = true

    if (isEditing.value && currentRoleId.value) {
      const updateData: RoleUpdate = {
        name: roleForm.name,
        description: roleForm.description,
        is_active: roleForm.is_active
      }
      await permissionApi.updateRole(currentRoleId.value, updateData)
      ElMessage.success('更新成功')
    } else {
      await permissionApi.createRole(roleForm)
      ElMessage.success('创建成功')
    }

    roleDialogVisible.value = false
    fetchRoles()
  } catch (error: any) {
    if (error?.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    }
  } finally {
    submitting.value = false
  }
}

// Delete role
async function handleDelete(role: Role) {
  if (role.is_system) {
    ElMessage.warning('系统内置角色不能删除')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除角色"${role.name}"吗？`,
      '确认删除',
      { type: 'warning' }
    )

    await permissionApi.deleteRole(role.id)
    ElMessage.success('删除成功')
    fetchRoles()
  } catch (error: any) {
    if (error !== 'cancel' && error?.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    }
  }
}

// Show permission dialog
async function showPermissionDialog(role: Role) {
  selectedRole.value = null
  selectedPermissionIds.value = new Set()
  permissionDialogVisible.value = true
  loadingPermissions.value = true

  try {
    // Load resources if not loaded
    if (resources.value.length === 0) {
      resources.value = await permissionApi.getResources()
    }

    // Load role with permissions
    const roleDetail = await permissionApi.getRoleById(role.id)
    selectedRole.value = roleDetail

    // Build permission ID set
    selectedPermissionIds.value = new Set(
      roleDetail.permissions.map(p => p.id)
    )
  } catch (error) {
    console.error('Failed to load permissions:', error)
    ElMessage.error('加载权限失败')
  } finally {
    loadingPermissions.value = false
  }
}

// Check if role has specific permission
function hasPermission(resourceCode: string, action: string): boolean {
  const resource = resources.value.find(r => r.code === resourceCode)
  if (!resource) return false

  const permission = resource.permissions.find(p => p.action === action)
  if (!permission) return false

  return selectedPermissionIds.value.has(permission.id)
}

// Toggle permission
function togglePermission(resourceCode: string, action: string, checked: boolean) {
  const resource = resources.value.find(r => r.code === resourceCode)
  if (!resource) return

  const permission = resource.permissions.find(p => p.action === action)
  if (!permission) return

  if (checked) {
    selectedPermissionIds.value.add(permission.id)
  } else {
    selectedPermissionIds.value.delete(permission.id)
  }
}

// Save permissions
async function savePermissions() {
  if (!selectedRole.value) return

  savingPermissions.value = true
  try {
    await permissionApi.updateRolePermissions(selectedRole.value.id, {
      permission_ids: Array.from(selectedPermissionIds.value)
    })
    ElMessage.success('权限保存成功')
    permissionDialogVisible.value = false
  } catch (error: any) {
    if (error?.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    }
  } finally {
    savingPermissions.value = false
  }
}

function formatDate(dateStr?: string) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchRoles()
})
</script>

<style scoped lang="scss">
.role-management {
  padding: 20px;

  .page-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .permission-header {
    margin-bottom: 16px;
    font-size: 14px;
    color: #606266;

    .role-code {
      margin-left: 8px;
      color: #909399;
    }
  }
}
</style>
