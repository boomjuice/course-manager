<template>
  <div class="teacher-view">
    <div class="page-header">
      <h1>教师管理</h1>
      <el-button v-permission="['teacher', 'edit']" type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon>
        新增教师
      </el-button>
    </div>

    <!-- Search Bar -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索姓名/电话..."
        clearable
        style="width: 220px"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="filterStatus" placeholder="教师状态" clearable style="width: 120px">
        <el-option
          v-for="item in statusOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-select
        v-model="filterSubjects"
        multiple
        collapse-tags
        collapse-tags-tooltip
        placeholder="科目"
        clearable
        style="width: 160px"
      >
        <el-option
          v-for="item in subjectOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-select
        v-model="filterGrades"
        multiple
        collapse-tags
        collapse-tags-tooltip
        placeholder="年级"
        clearable
        style="width: 160px"
      >
        <el-option
          v-for="item in gradeOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-button @click="handleSearch">搜索</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- Table -->
    <el-table :data="teachers" v-loading="loading" stripe>
      <el-table-column prop="name" label="姓名" min-width="80" />
      <el-table-column prop="phone" label="电话" min-width="120" />
      <el-table-column prop="gender" label="性别" width="60" align="center">
        <template #default="{ row }">
          {{ getGenderLabel(row.gender) }}
        </template>
      </el-table-column>
      <el-table-column prop="subjects" label="负责科目" min-width="150">
        <template #default="{ row }">
          <template v-if="row.subjects && row.subjects.length">
            <el-tag
              v-for="subj in row.subjects"
              :key="subj"
              size="small"
              :color="getSubjectColor(subj)"
              style="margin-right: 4px; margin-bottom: 2px; color: #fff; border: none;"
            >
              {{ getSubjectLabel(subj) }}
            </el-tag>
          </template>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="grade_levels" label="负责年级" min-width="180">
        <template #default="{ row }">
          <template v-if="row.grade_levels && row.grade_levels.length">
            <el-tag
              v-for="grade in row.grade_levels"
              :key="grade"
              size="small"
              type="info"
              style="margin-right: 4px; margin-bottom: 2px;"
            >
              {{ getGradeLabel(grade) }}
            </el-tag>
          </template>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="hourly_rate" label="课时费" min-width="90" align="right">
        <template #default="{ row }">
          <span class="price">¥{{ Number(row.hourly_rate || 0).toFixed(0) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="70" align="center">
        <template #default="{ row }">
          <el-tag size="small" :type="getStatusType(row.status)">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_time" label="创建时间" width="170">
        <template #default="{ row }">
          {{ formatDate(row.created_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button v-permission="['teacher', 'edit']" link type="primary" size="small" @click="showDialog(row)">编辑</el-button>
          <el-popconfirm title="确定删除该教师？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button v-permission="['teacher', 'delete']" link type="danger" size="small">删除</el-button>
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
      :title="editingItem ? '编辑教师' : '新增教师'"
      width="600px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="form.name" placeholder="请输入教师姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话" prop="phone">
              <el-input v-model="form.phone" placeholder="必填，用于创建登录账号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="性别" prop="gender">
              <el-select v-model="form.gender" placeholder="请选择" style="width: 100%">
                <el-option
                  v-for="item in genderOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="入职日期" prop="hire_date">
              <el-date-picker
                v-model="form.hire_date"
                type="date"
                placeholder="选择日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="负责科目" prop="subjects">
          <el-select
            v-model="form.subjects"
            multiple
            placeholder="请选择负责科目"
            style="width: 100%"
          >
            <el-option
              v-for="item in subjectOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="负责年级" prop="grade_levels">
          <el-select
            v-model="form.grade_levels"
            multiple
            placeholder="请选择负责年级"
            style="width: 100%"
          >
            <el-option
              v-for="item in gradeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="专业" prop="major">
              <el-input v-model="form.major" placeholder="请输入专业" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="课时费" prop="hourly_rate">
              <el-input-number
                v-model="form.hourly_rate"
                :min="0"
                :precision="2"
                :step="10"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="教师状态" prop="status">
          <el-select v-model="form.status" placeholder="请选择" style="width: 200px">
            <el-option
              v-for="item in statusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="notes">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="备注信息" />
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
  getTeachers, createTeacher, updateTeacher, deleteTeacher,
  type Teacher, type TeacherCreate
} from '@/api/teacher'
import { getDictItems, type DictItem } from '@/api/dictionary'

// State
const teachers = ref<Teacher[]>([])
const loading = ref(false)
const saving = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const filterStatus = ref('')
const filterSubjects = ref<string[]>([])
const filterGrades = ref<string[]>([])

// Dictionary options
const genderOptions = ref<DictItem[]>([])
const statusOptions = ref<DictItem[]>([])
const subjectOptions = ref<DictItem[]>([])
const gradeOptions = ref<DictItem[]>([])

// Dialog
const dialogVisible = ref(false)
const editingItem = ref<Teacher | null>(null)
const formRef = ref<FormInstance>()
const form = ref<TeacherCreate>({
  name: '',
  phone: '',
  gender: '',
  education: '',
  major: '',
  subjects: [],
  grade_levels: [],
  hire_date: '',
  status: 'active',
  hourly_rate: 0,
  introduction: '',
  notes: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入教师姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入联系电话（用于创建登录账号）', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
}

// Methods
const getGenderLabel = (value?: string) => {
  if (!value) return '-'
  return genderOptions.value.find(i => i.value === value)?.label || value
}

const getStatusLabel = (value: string) => {
  return statusOptions.value.find(i => i.value === value)?.label || value
}

const getStatusType = (status: string) => {
  // 从数据字典取颜色（color字段存储el-tag的type值）
  return statusOptions.value.find(i => i.value === status)?.color || 'info'
}

const getSubjectLabel = (value: string) => {
  return subjectOptions.value.find(i => i.value === value)?.label || value
}

const getSubjectColor = (value: string) => {
  return subjectOptions.value.find(i => i.value === value)?.color || '#6B7280'
}

const getGradeLabel = (value: string) => {
  return gradeOptions.value.find(i => i.value === value)?.label || value
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadDictionaries = async () => {
  try {
    const [genderRes, statusRes, subjectRes, gradeRes] = await Promise.all([
      getDictItems('gender'),
      getDictItems('teacher_status'),
      getDictItems('subject'),
      getDictItems('grade'),
    ])
    genderOptions.value = genderRes || []
    statusOptions.value = statusRes || []
    subjectOptions.value = subjectRes || []
    gradeOptions.value = gradeRes || []
  } catch {
    // 字典加载失败不影响页面使用
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getTeachers({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchKeyword.value || undefined,
      status: filterStatus.value || undefined,
      subjects: filterSubjects.value.length ? filterSubjects.value : undefined,
      grade_levels: filterGrades.value.length ? filterGrades.value : undefined,
    })
    teachers.value = res.data?.items || []
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
  filterStatus.value = ''
  filterSubjects.value = []
  filterGrades.value = []
  currentPage.value = 1
  loadData()
}

const showDialog = (item?: Teacher) => {
  editingItem.value = item || null
  if (item) {
    form.value = {
      name: item.name,
      phone: item.phone || '',
      gender: item.gender || '',
      education: item.education || '',
      major: item.major || '',
      subjects: item.subjects || [],
      grade_levels: item.grade_levels || [],
      hire_date: item.hire_date || '',
      status: item.status,
      hourly_rate: item.hourly_rate,
      introduction: item.introduction || '',
      notes: item.notes || '',
    }
  } else {
    form.value = {
      name: '',
      phone: '',
      gender: genderOptions.value[0]?.value || '',
      education: '',
      major: '',
      subjects: [],
      grade_levels: [],
      hire_date: '',
      status: 'active',
      hourly_rate: 0,
      introduction: '',
      notes: '',
    }
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  await formRef.value?.validate()
  saving.value = true
  try {
    // 处理空字符串字段，转成undefined避免后端验证错误
    const data = {
      ...form.value,
      phone: form.value.phone || undefined,
      gender: form.value.gender || undefined,
      education: form.value.education || undefined,
      major: form.value.major || undefined,
      hire_date: form.value.hire_date || undefined,
      introduction: form.value.introduction || undefined,
      notes: form.value.notes || undefined,
      subjects: form.value.subjects?.length ? form.value.subjects : undefined,
      grade_levels: form.value.grade_levels?.length ? form.value.grade_levels : undefined,
    }
    if (editingItem.value) {
      await updateTeacher(editingItem.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await createTeacher(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteTeacher(id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => {
  loadDictionaries()
  loadData()
})
</script>

<style scoped lang="scss">
.teacher-view {
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

.price {
  font-weight: 600;
  color: var(--primary-500);
}

.text-muted {
  color: #9ca3af;
}
</style>
