<template>
  <div class="campus-view">
    <div class="page-header">
      <h1>校区管理</h1>
      <el-button v-permission="['campus', 'edit']" type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon>
        新增校区
      </el-button>
    </div>

    <!-- Search Bar -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索校区名称..."
        clearable
        style="width: 300px"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px">
        <el-option label="启用" :value="true" />
        <el-option label="禁用" :value="false" />
      </el-select>
      <el-button @click="handleSearch">搜索</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- Table -->
    <el-table :data="campuses" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="name" label="校区名称" min-width="150" />
      <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
      <el-table-column prop="phone" label="联系电话" width="140" />
      <el-table-column prop="classrooms" label="教室数" width="100" align="center">
        <template #default="{ row }">
          <el-tag type="info">{{ row.classrooms?.length || 0 }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_time" label="创建时间" width="170">
        <template #default="{ row }">
          {{ formatDate(row.created_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button v-permission="['campus', 'edit']" link type="primary" @click="showDialog(row)">编辑</el-button>
          <el-popconfirm
            title="确定删除该校区？删除后关联的教室也会被删除！"
            @confirm="handleDelete(row.id)"
          >
            <template #reference>
              <el-button v-permission="['campus', 'delete']" link type="danger">删除</el-button>
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

    <!-- Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingItem ? '编辑校区' : '新增校区'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="校区名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入校区名称" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="form.address" type="textarea" :rows="2" placeholder="请输入地址" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入联系电话" />
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  getCampuses, createCampus, updateCampus, deleteCampus,
  type Campus, type CampusCreate
} from '@/api/campus'

// State
const campuses = ref<Campus[]>([])
const loading = ref(false)
const saving = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const filterStatus = ref<boolean | undefined>(undefined)

// Dialog
const dialogVisible = ref(false)
const editingItem = ref<Campus | null>(null)
const formRef = ref<FormInstance>()
const form = ref<CampusCreate>({
  name: '',
  address: '',
  phone: '',
  is_active: true,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入校区名称', trigger: 'blur' }],
}

// Methods
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getCampuses({
      include_inactive: filterStatus.value === false ? true : filterStatus.value === undefined,
    })
    // 后端返回数组，前端做过滤和分页
    let data = res || []
    // 搜索过滤
    if (searchKeyword.value) {
      const kw = searchKeyword.value.toLowerCase()
      data = data.filter((c: Campus) => c.name.toLowerCase().includes(kw) || c.address?.toLowerCase().includes(kw))
    }
    // 状态过滤
    if (filterStatus.value !== undefined) {
      data = data.filter((c: Campus) => c.is_active === filterStatus.value)
    }
    total.value = data.length
    // 分页
    const start = (currentPage.value - 1) * pageSize.value
    campuses.value = data.slice(start, start + pageSize.value)
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
  filterStatus.value = undefined
  currentPage.value = 1
  loadData()
}

const showDialog = (item?: Campus) => {
  editingItem.value = item || null
  if (item) {
    form.value = {
      name: item.name,
      address: item.address || '',
      phone: item.phone || '',
      is_active: item.is_active,
    }
  } else {
    form.value = { name: '', address: '', phone: '', is_active: true }
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (editingItem.value) {
      await updateCampus(editingItem.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createCampus(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteCampus(id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.campus-view {
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
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
