<template>
  <div class="classroom-view">
    <div class="page-header">
      <h1>教室管理</h1>
      <el-button v-permission="['classroom', 'edit']" type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon>
        新增教室
      </el-button>
    </div>

    <!-- Search Bar -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索教室名称..."
        clearable
        style="width: 250px"
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
    <el-table :data="classrooms" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="name" label="教室名称" min-width="150" />
      <el-table-column prop="capacity" label="容量" width="100" align="center">
        <template #default="{ row }">
          <span v-if="row.capacity">{{ row.capacity }}人</span>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column label="设备配置" min-width="200">
        <template #default="{ row }">
          <template v-if="row.equipment && Object.keys(row.equipment).length">
            <el-tag
              v-for="(value, key) in row.equipment"
              :key="key"
              size="small"
              style="margin-right: 4px; margin-bottom: 2px;"
            >
              {{ key }}: {{ value }}
            </el-tag>
          </template>
          <span v-else class="text-muted">-</span>
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
          <el-button v-permission="['classroom', 'edit']" link type="primary" @click="showDialog(row)">编辑</el-button>
          <el-popconfirm title="确定删除该教室？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button v-permission="['classroom', 'delete']" link type="danger">删除</el-button>
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
      :title="editingItem ? '编辑教室' : '新增教室'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="所属校区" prop="campus_id">
          <el-select v-model="form.campus_id" placeholder="请选择校区" style="width: 100%">
            <el-option
              v-for="c in allCampuses"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="教室名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入教室名称" />
        </el-form-item>
        <el-form-item label="容量" prop="capacity">
          <el-input-number v-model="form.capacity" :min="1" :max="500" placeholder="可容纳人数" />
        </el-form-item>
        <el-form-item label="设备配置">
          <div class="equipment-list">
            <div
              v-for="(item, index) in equipmentList"
              :key="index"
              class="equipment-item"
            >
              <el-input
                v-model="item.key"
                placeholder="设备名称"
                style="width: 120px"
              />
              <span class="separator">:</span>
              <el-input
                v-model="item.value"
                placeholder="数量/状态"
                style="width: 120px"
              />
              <el-button
                type="danger"
                :icon="Delete"
                circle
                size="small"
                @click="removeEquipment(index)"
              />
            </div>
            <el-button type="primary" :icon="Plus" @click="addEquipment">
              添加设备
            </el-button>
          </div>
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
import { Plus, Search, Delete } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  getClassrooms, createClassroom, updateClassroom, deleteClassroom,
  getAllCampuses,
  type Classroom, type ClassroomCreate, type Campus
} from '@/api/campus'

// State
const classrooms = ref<Classroom[]>([])
const allCampuses = ref<Campus[]>([])  // 用于新建教室时选择校区
const loading = ref(false)
const saving = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const filterStatus = ref<boolean | undefined>(undefined)

// Dialog
const dialogVisible = ref(false)
const editingItem = ref<Classroom | null>(null)
const formRef = ref<FormInstance>()
const form = ref<ClassroomCreate>({
  campus_id: 0,
  name: '',
  capacity: undefined,
  equipment: undefined,
  is_active: true,
})

// 设备配置列表（用于动态key-value编辑）
interface EquipmentItem {
  key: string
  value: string
}
const equipmentList = ref<EquipmentItem[]>([])

// 添加设备配置
const addEquipment = () => {
  equipmentList.value.push({ key: '', value: '' })
}

// 删除设备配置
const removeEquipment = (index: number) => {
  equipmentList.value.splice(index, 1)
}

// 将equipmentList转换为Record<string, string>
const equipmentListToRecord = (): Record<string, string> | undefined => {
  const result: Record<string, string> = {}
  for (const item of equipmentList.value) {
    if (item.key.trim()) {
      result[item.key.trim()] = item.value.trim()
    }
  }
  return Object.keys(result).length > 0 ? result : undefined
}

// 将Record<string, string>转换为equipmentList
const recordToEquipmentList = (record?: Record<string, string>) => {
  if (!record) {
    equipmentList.value = []
    return
  }
  equipmentList.value = Object.entries(record).map(([key, value]) => ({ key, value }))
}

const rules: FormRules = {
  campus_id: [{ required: true, message: '请选择校区', trigger: 'change' }],
  name: [{ required: true, message: '请输入教室名称', trigger: 'blur' }],
}

// Methods
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadCampuses = async () => {
  const res = await getAllCampuses(true)
  allCampuses.value = res || []
}

const loadData = async () => {
  loading.value = true
  try {
    // 后端已做校区过滤，这里只需要传状态过滤
    const res = await getClassrooms({
      active_only: filterStatus.value === true ? true : filterStatus.value === false ? false : undefined,
    })
    // 后端返回数组，前端做搜索过滤和分页
    let data = res || []
    // 搜索过滤（名称）
    if (searchKeyword.value) {
      const kw = searchKeyword.value.toLowerCase()
      data = data.filter((c: Classroom) => c.name.toLowerCase().includes(kw))
    }
    // 状态过滤（如果后端没处理好，前端再过滤一次）
    if (filterStatus.value !== undefined) {
      data = data.filter((c: Classroom) => c.is_active === filterStatus.value)
    }
    total.value = data.length
    // 分页
    const start = (currentPage.value - 1) * pageSize.value
    classrooms.value = data.slice(start, start + pageSize.value)
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

const showDialog = (item?: Classroom) => {
  editingItem.value = item || null
  if (item) {
    form.value = {
      campus_id: item.campus_id,
      name: item.name,
      capacity: item.capacity,
      equipment: item.equipment,
      is_active: item.is_active,
    }
    // 初始化设备配置列表
    recordToEquipmentList(item.equipment)
  } else {
    form.value = {
      campus_id: allCampuses.value[0]?.id || 0,
      name: '',
      capacity: undefined,
      equipment: undefined,
      is_active: true,
    }
    // 清空设备配置列表
    equipmentList.value = []
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  await formRef.value?.validate()
  saving.value = true
  try {
    // 将设备列表转换为Record格式
    const data = {
      ...form.value,
      equipment: equipmentListToRecord(),
    }
    if (editingItem.value) {
      await updateClassroom(editingItem.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await createClassroom(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteClassroom(id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => {
  loadCampuses()
  loadData()
})
</script>

<style scoped lang="scss">
.classroom-view {
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

.text-muted {
  color: var(--gray-400);
}

// 设备配置编辑样式
.equipment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.equipment-item {
  display: flex;
  align-items: center;
  gap: 8px;

  .separator {
    color: var(--text-secondary);
    font-weight: bold;
  }
}
</style>
