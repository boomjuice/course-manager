<template>
  <div class="course-view">
    <div class="page-header">
      <h1>课程产品</h1>
      <el-button v-permission="['course', 'edit']" type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon>
        新增课程
      </el-button>
    </div>

    <!-- Search Bar -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索课程名称/编码..."
        clearable
        style="width: 250px"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="filterSubject" placeholder="学科" clearable style="width: 120px">
        <el-option
          v-for="item in subjectOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-select v-model="filterGrade" placeholder="年级" clearable style="width: 120px">
        <el-option
          v-for="item in gradeOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-select v-model="filterLevel" placeholder="难度" clearable style="width: 100px">
        <el-option
          v-for="item in levelOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
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
    <el-table :data="courses" v-loading="loading" stripe>
      <el-table-column prop="code" label="编码" min-width="100" />
      <el-table-column prop="name" label="课程名称" min-width="150" show-overflow-tooltip />
      <el-table-column prop="subject" label="学科" min-width="80">
        <template #default="{ row }">
          <el-tag
            v-if="row.subject"
            size="small"
            :color="getSubjectColor(row.subject)"
            style="color: #fff; border: none;"
          >
            {{ getSubjectLabel(row.subject) }}
          </el-tag>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="grade_level" label="年级" min-width="80">
        <template #default="{ row }">
          <el-tag v-if="row.grade_level" size="small" type="info">
            {{ getGradeLabel(row.grade_level) }}
          </el-tag>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="level" label="难度" min-width="70">
        <template #default="{ row }">
          <el-tag v-if="row.level" size="small" :type="getLevelType(row.level)">{{ getLevelLabel(row.level) }}</el-tag>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="unit_price" label="课时单价" width="90" align="right">
        <template #default="{ row }">
          <span class="price">¥{{ Number(row.unit_price || 0).toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="70" align="center">
        <template #default="{ row }">
          <el-tag size="small" :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '启用' : '禁用' }}
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
          <el-button v-permission="['course', 'edit']" link type="primary" size="small" @click="showDialog(row)">编辑</el-button>
          <el-popconfirm title="确定删除该课程？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button v-permission="['course', 'delete']" link type="danger" size="small">删除</el-button>
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
      :title="editingItem ? '编辑课程' : '新增课程'"
      width="600px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="课程编码" prop="code">
              <el-input v-model="form.code" placeholder="如: MATH001" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="课程名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入课程名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学科" prop="subject">
              <el-select v-model="form.subject" placeholder="请选择学科" style="width: 100%">
                <el-option
                  v-for="item in subjectOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="年级" prop="grade_level">
              <el-select v-model="form.grade_level" placeholder="请选择年级" style="width: 100%">
                <el-option
                  v-for="item in gradeOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="难度等级" prop="level">
              <el-select v-model="form.level" placeholder="请选择难度" style="width: 100%">
                <el-option
                  v-for="item in levelOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="课时单价" prop="unit_price">
              <el-input-number v-model="form.unit_price" :min="0" :precision="2" style="width: 100%" />
              <div class="form-tip">开班时可单独设置价格</div>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="课程描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入课程描述"
          />
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
  getCourseProducts, createCourseProduct, updateCourseProduct, deleteCourseProduct,
  type CourseProduct, type CourseProductCreate
} from '@/api/course'
import { getDictItems, type DictItem } from '@/api/dictionary'

// State
const courses = ref<CourseProduct[]>([])
const loading = ref(false)
const saving = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const filterSubject = ref('')
const filterGrade = ref('')
const filterLevel = ref('')
const filterStatus = ref<boolean | undefined>(undefined)

// Dictionary options
const subjectOptions = ref<DictItem[]>([])
const gradeOptions = ref<DictItem[]>([])
const levelOptions = ref<DictItem[]>([])

// Dialog
const dialogVisible = ref(false)
const editingItem = ref<CourseProduct | null>(null)
const formRef = ref<FormInstance>()
const form = ref<CourseProductCreate>({
  code: '',
  name: '',
  subject: '',
  grade_level: '',
  level: '',
  description: '',
  unit_price: 0,
  is_active: true,
})

const rules: FormRules = {
  code: [{ required: true, message: '请输入课程编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入课程名称', trigger: 'blur' }],
}

// Methods
const getSubjectLabel = (value: string) => {
  return subjectOptions.value.find(i => i.value === value)?.label || value
}

const getSubjectColor = (value: string) => {
  return subjectOptions.value.find(i => i.value === value)?.color || '#6B7280'
}

const getGradeLabel = (value: string) => {
  return gradeOptions.value.find(i => i.value === value)?.label || value
}

const getLevelLabel = (value: string) => {
  return levelOptions.value.find(i => i.value === value)?.label || value
}

const getLevelType = (level: string) => {
  // 从数据字典取颜色（color字段存储el-tag的type值）
  return levelOptions.value.find(i => i.value === level)?.color || 'info'
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadDictionaries = async () => {
  try {
    const [subjectRes, gradeRes, levelRes] = await Promise.all([
      getDictItems('subject'),
      getDictItems('grade'),
      getDictItems('course_level'),
    ])
    subjectOptions.value = subjectRes || []
    gradeOptions.value = gradeRes || []
    levelOptions.value = levelRes || []
  } catch {
    // 字典加载失败不影响页面使用
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getCourseProducts({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchKeyword.value || undefined,
      subject: filterSubject.value || undefined,
      grade_level: filterGrade.value || undefined,
      level: filterLevel.value || undefined,
      is_active: filterStatus.value,
    })
    courses.value = res.data?.items || []
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
  filterSubject.value = ''
  filterGrade.value = ''
  filterLevel.value = ''
  filterStatus.value = undefined
  currentPage.value = 1
  loadData()
}

const showDialog = (item?: CourseProduct) => {
  editingItem.value = item || null
  if (item) {
    form.value = {
      code: item.code,
      name: item.name,
      subject: item.subject || '',
      grade_level: item.grade_level || '',
      level: item.level || '',
      description: item.description || '',
      unit_price: item.unit_price || 0,
      is_active: item.is_active,
    }
  } else {
    form.value = {
      code: '',
      name: '',
      subject: subjectOptions.value[0]?.value || '',
      grade_level: gradeOptions.value[0]?.value || '',
      level: levelOptions.value[0]?.value || '',
      description: '',
      unit_price: 0,
      is_active: true,
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
      subject: form.value.subject || undefined,
      grade_level: form.value.grade_level || undefined,
      level: form.value.level || undefined,
      description: form.value.description || undefined,
    }
    if (editingItem.value) {
      await updateCourseProduct(editingItem.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await createCourseProduct(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteCourseProduct(id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => {
  loadDictionaries()
  loadData()
})
</script>

<style scoped lang="scss">
.course-view {
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

.text-muted {
  color: var(--gray-400);
}

.price {
  font-weight: 600;
  color: var(--danger-500);
}

.form-tip {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}
</style>
