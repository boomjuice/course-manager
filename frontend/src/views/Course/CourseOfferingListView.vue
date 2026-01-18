<template>
  <div class="classplan-view">
    <div class="page-header">
      <h1>开班计划</h1>
      <el-button v-permission="['class_plan', 'edit']" type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon>
        新增开班
      </el-button>
    </div>

    <!-- Search Bar -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索班级名称..."
        clearable
        style="width: 200px"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px">
        <el-option
          v-for="item in statusOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-select v-model="filterCourse" placeholder="课程" clearable style="width: 150px">
        <el-option
          v-for="c in allCourses"
          :key="c.id"
          :label="c.name"
          :value="c.id"
        />
      </el-select>
      <el-select v-model="filterTeacher" placeholder="教师" clearable style="width: 120px">
        <el-option
          v-for="t in allTeachers"
          :key="t.id"
          :label="t.name"
          :value="t.id"
        />
      </el-select>
      <el-date-picker
        v-model="filterDateRange"
        type="daterange"
        range-separator="-"
        start-placeholder="开班日期起"
        end-placeholder="开班日期止"
        value-format="YYYY-MM-DD"
        style="width: 240px"
        clearable
      />
      <el-button @click="handleSearch">搜索</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- Table -->
    <el-table :data="classPlans" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="name" label="班级名称" min-width="150" fixed="left" />
      <el-table-column prop="course_name" label="课程" min-width="150">
        <template #default="{ row }">
          {{ row.course_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="teacher_name" label="教师" width="100">
        <template #default="{ row }">
          {{ row.teacher_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="classroom_name" label="教室" width="120">
        <template #default="{ row }">
          {{ row.classroom_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="人数" width="100" align="center">
        <template #default="{ row }">
          <el-tag
            :type="row.current_students >= row.max_students ? 'danger' : 'success'"
            class="clickable-tag"
            @click="showStudentsDialog(row)"
          >
            {{ row.current_students }}/{{ row.max_students }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="start_date" label="开班日期" width="110" />
      <el-table-column prop="end_date" label="结班日期" width="110" />
      <el-table-column prop="status" label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_time" label="创建时间" width="170">
        <template #default="{ row }">
          {{ formatDateTime(row.created_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button v-permission="['class_plan', 'edit']" link type="primary" @click="showDialog(row)">编辑</el-button>
          <el-popconfirm title="确定删除该开班计划？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button v-permission="['class_plan', 'delete']" link type="danger">删除</el-button>
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
      :title="editingItem ? '编辑开班计划' : '新增开班计划'"
      width="700px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="班级名称" prop="name">
              <el-input v-model="form.name" placeholder="如: 数学基础班A" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="课程" prop="course_id">
              <el-select v-model="form.course_id" placeholder="请选择课程" style="width: 100%">
                <el-option
                  v-for="c in allCourses"
                  :key="c.id"
                  :label="c.name"
                  :value="c.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="授课教师" prop="teacher_id">
              <el-select
                v-model="form.teacher_id"
                placeholder="请选择教师"
                style="width: 100%"
                :disabled="!form.course_id"
              >
                <el-option-group v-if="matchedTeachers.length > 0" label="推荐教师（科目/年级匹配）">
                  <el-option
                    v-for="t in matchedTeachers"
                    :key="t.id"
                    :label="t.name"
                    :value="t.id"
                  >
                    <span>{{ t.name }}</span>
                    <span style="color: var(--success-500); margin-left: 8px; font-size: 12px;">✓ 匹配</span>
                  </el-option>
                </el-option-group>
                <el-option-group v-if="unmatchedTeachers.length > 0" label="其他教师">
                  <el-option
                    v-for="t in unmatchedTeachers"
                    :key="t.id"
                    :label="t.name"
                    :value="t.id"
                  />
                </el-option-group>
              </el-select>
              <div v-if="selectedCourse && (selectedCourse.subject || selectedCourse.grade_level)" class="matching-hint">
                <el-icon><InfoFilled /></el-icon>
                <span>
                  匹配条件:
                  <template v-if="selectedCourse.subject">{{ getSubjectLabel(selectedCourse.subject) }}</template>
                  <template v-if="selectedCourse.subject && selectedCourse.grade_level"> + </template>
                  <template v-if="selectedCourse.grade_level">{{ getGradeLabel(selectedCourse.grade_level) }}</template>
                </span>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="教室" prop="classroom_id">
              <el-select
                v-model="form.classroom_id"
                placeholder="请选择教室"
                style="width: 100%"
                clearable
              >
                <el-option
                  v-for="r in allClassrooms"
                  :key="r.id"
                  :label="`${r.name} (${r.campus?.name || ''})`"
                  :value="r.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="班级状态" prop="status">
              <el-select v-model="form.status" placeholder="请选择" style="width: 100%">
                <el-option
                  v-for="item in statusOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="最大人数" prop="max_students">
              <el-input-number v-model="form.max_students" :min="1" :max="100" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="总课次" prop="total_lessons">
              <el-input-number v-model="form.total_lessons" :min="0" :step="0.5" :precision="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8" v-if="editingItem">
            <el-form-item label="当前人数">
              <el-input :model-value="form.current_students" disabled style="width: 100%">
                <template #suffix>
                  <span style="color: var(--text-tertiary); font-size: 12px;">由报名自动计算</span>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开班日期" prop="start_date">
              <el-date-picker
                v-model="form.start_date"
                type="date"
                placeholder="选择日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结班日期" prop="end_date">
              <el-date-picker
                v-model="form.end_date"
                type="date"
                placeholder="选择日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="上课安排" prop="schedule">
          <el-input
            v-model="form.schedule"
            type="textarea"
            :rows="2"
            placeholder="如: 每周六、日 9:00-11:00"
          />
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

    <!-- 学生列表弹窗 -->
    <el-dialog
      v-model="studentsDialogVisible"
      :title="`${selectedClassPlan?.name || ''} - 已报名学生`"
      width="650px"
    >
      <el-table :data="enrolledStudents" v-loading="loadingStudents" stripe size="small">
        <el-table-column label="学生" width="100">
          <template #default="{ row }">
            {{ row.student?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="联系电话" width="130">
          <template #default="{ row }">
            {{ row.student?.phone || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="报名日期" width="110">
          <template #default="{ row }">
            {{ formatDate(row.enroll_date) }}
          </template>
        </el-table-column>
        <el-table-column label="课时" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="Number(row.used_hours) >= Number(row.purchased_hours) ? 'danger' : 'success'">
              {{ row.used_hours }}/{{ row.purchased_hours }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="付款金额" width="100" align="right">
          <template #default="{ row }">
            <span class="price">¥{{ Number(row.paid_amount || 0).toFixed(0) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="getEnrollmentStatusType(row.status)">
              {{ getEnrollmentStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="studentsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Plus, Search, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  getClassPlans, createClassPlan, updateClassPlan, deleteClassPlan,
  type ClassPlan, type ClassPlanCreate
} from '@/api/classplan'
import { getEnrollments, type Enrollment } from '@/api/enrollment'
import { getAllCourseProducts, type CourseProduct } from '@/api/course'
import { getAllTeachers, type Teacher } from '@/api/teacher'
import { getAllClassrooms, type Classroom } from '@/api/campus'
import { getDictItems, type DictItem } from '@/api/dictionary'

// 报名状态字典（用于学生弹窗）
const enrollmentStatusOptions = ref<DictItem[]>([])

// State
const classPlans = ref<ClassPlan[]>([])
const loading = ref(false)
const saving = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const filterStatus = ref('')
const filterCourse = ref<number | undefined>(undefined)
const filterTeacher = ref<number | undefined>(undefined)
const filterDateRange = ref<[string, string] | null>(null)

// Options
const allCourses = ref<CourseProduct[]>([])
const allTeachers = ref<Teacher[]>([])
const allClassrooms = ref<Classroom[]>([])
const statusOptions = ref<DictItem[]>([])
const subjectOptions = ref<DictItem[]>([])
const gradeOptions = ref<DictItem[]>([])

// Dialog
const dialogVisible = ref(false)
const editingItem = ref<ClassPlan | null>(null)
const formRef = ref<FormInstance>()

// 学生列表弹窗
const studentsDialogVisible = ref(false)
const selectedClassPlan = ref<ClassPlan | null>(null)
const enrolledStudents = ref<Enrollment[]>([])
const loadingStudents = ref(false)

const form = ref<ClassPlanCreate>({
  name: '',
  course_id: 0,
  teacher_id: 0,
  classroom_id: undefined,
  max_students: 20,
  current_students: 0,
  total_lessons: 0,
  start_date: '',
  end_date: '',
  status: 'enrolling',
  schedule: '',
  notes: '',
})

// 自定义校验：结班日期不能早于今天（新建时）
const validateEndDate = (_rule: any, value: string, callback: any) => {
  if (!value) {
    callback()  // 允许为空
    return
  }
  // 编辑已完成或已取消的班级时，不校验结班日期
  if (editingItem.value && ['completed', 'cancelled'].includes(editingItem.value.status)) {
    callback()
    return
  }
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const endDate = new Date(value)
  if (endDate < today) {
    callback(new Error('结班日期不能早于今天'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  name: [{ required: true, message: '请输入班级名称', trigger: 'blur' }],
  course_id: [{ required: true, message: '请选择课程', trigger: 'change' }],
  teacher_id: [{ required: true, message: '请选择教师', trigger: 'change' }],
  end_date: [{ validator: validateEndDate, trigger: 'change' }],
}

// 当前选中的课程
const selectedCourse = computed(() => {
  return allCourses.value.find(c => c.id === form.value.course_id)
})

// 匹配的教师（科目和年级都匹配）
const matchedTeachers = computed(() => {
  const course = selectedCourse.value
  if (!course) return []

  return allTeachers.value.filter(teacher => {
    // 如果课程没有设置学科和年级，则所有教师都匹配
    if (!course.subject && !course.grade_level) return true

    let subjectMatch = true
    let gradeMatch = true

    // 检查科目匹配
    if (course.subject) {
      subjectMatch = (teacher.subjects || []).includes(course.subject)
    }

    // 检查年级匹配
    if (course.grade_level) {
      gradeMatch = (teacher.grade_levels || []).includes(course.grade_level)
    }

    return subjectMatch && gradeMatch
  })
})

// 不匹配的教师
const unmatchedTeachers = computed(() => {
  const matched = matchedTeachers.value
  return allTeachers.value.filter(t => !matched.find(m => m.id === t.id))
})

// Methods
const getStatusLabel = (value: string) => {
  return statusOptions.value.find(i => i.value === value)?.label || value
}

const getSubjectLabel = (value: string) => {
  return subjectOptions.value.find(i => i.value === value)?.label || value
}

const getGradeLabel = (value: string) => {
  return gradeOptions.value.find(i => i.value === value)?.label || value
}

const getStatusType = (status: string) => {
  // 从数据字典取颜色（color字段存储el-tag的type值）
  return statusOptions.value.find(i => i.value === status)?.color || 'info'
}

// 报名状态相关 - 从数据字典取
const getEnrollmentStatusLabel = (status: string) => {
  return enrollmentStatusOptions.value.find(i => i.value === status)?.label || status
}

const getEnrollmentStatusType = (status: string) => {
  return enrollmentStatusOptions.value.find(i => i.value === status)?.color || 'info'
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return `${d.toLocaleDateString('zh-CN')} ${d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`
}

// 显示学生列表弹窗
const showStudentsDialog = async (classPlan: ClassPlan) => {
  selectedClassPlan.value = classPlan
  studentsDialogVisible.value = true
  loadingStudents.value = true
  try {
    const res = await getEnrollments({
      class_plan_id: classPlan.id,
      page_size: 100, // 获取该班所有学生
    })
    enrolledStudents.value = res.data?.items || []
  } finally {
    loadingStudents.value = false
  }
}

// 当选择课程变化时，自动选择第一个匹配的教师（仅在新建时）
watch(() => form.value.course_id, (newCourseId) => {
  if (!editingItem.value && newCourseId) {
    // 新建模式下，自动选择第一个匹配的教师
    const matched = matchedTeachers.value
    if (matched.length > 0 && matched[0]) {
      form.value.teacher_id = matched[0].id
    }
  }
})

const loadOptions = async () => {
  try {
    const [coursesRes, teachersRes, classroomsRes, statusRes, subjectRes, gradeRes, enrollStatusRes] = await Promise.all([
      getAllCourseProducts(true),
      getAllTeachers(true),
      getAllClassrooms(undefined, true),
      getDictItems('class_status'),
      getDictItems('subject'),
      getDictItems('grade'),
      getDictItems('enrollment_status'),
    ])
    allCourses.value = coursesRes || []
    allTeachers.value = teachersRes || []
    allClassrooms.value = classroomsRes || []
    statusOptions.value = statusRes || []
    subjectOptions.value = subjectRes || []
    gradeOptions.value = gradeRes || []
    enrollmentStatusOptions.value = enrollStatusRes || []
  } catch {
    // 加载失败不影响页面使用
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getClassPlans({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchKeyword.value || undefined,
      status: filterStatus.value || undefined,
      course_id: filterCourse.value,
      teacher_id: filterTeacher.value,
      start_date_from: filterDateRange.value?.[0],
      start_date_to: filterDateRange.value?.[1],
    })
    classPlans.value = res.data?.items || []
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
  filterCourse.value = undefined
  filterTeacher.value = undefined
  filterDateRange.value = null
  currentPage.value = 1
  loadData()
}

const showDialog = (item?: ClassPlan) => {
  editingItem.value = item || null
  if (item) {
    form.value = {
      name: item.name,
      course_id: item.course_id,
      teacher_id: item.teacher_id ?? 0,
      classroom_id: item.classroom_id,
      max_students: item.max_students,
      current_students: item.current_students,
      total_lessons: item.total_lessons || 0,
      start_date: item.start_date || '',
      end_date: item.end_date || '',
      status: item.status,
      schedule: item.schedule || '',
      notes: item.notes || '',
    }
  } else {
    form.value = {
      name: '',
      course_id: allCourses.value[0]?.id || 0,
      teacher_id: allTeachers.value[0]?.id || 0,
      classroom_id: undefined,
      max_students: 20,
      current_students: 0,
      total_lessons: 0,
      start_date: '',
      end_date: '',
      status: 'enrolling',
      schedule: '',
      notes: '',
    }
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  await formRef.value?.validate()
  saving.value = true
  try {
    if (editingItem.value) {
      // 注意：current_students由报名自动计算，不应手动更新
      const { current_students, ...updateData } = form.value
      await updateClassPlan(editingItem.value.id, updateData)
      ElMessage.success('更新成功')
    } else {
      // 新建时也不需要传current_students，后端会初始化为0
      const { current_students, ...createData } = form.value
      await createClassPlan(createData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteClassPlan(id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => {
  loadOptions()
  loadData()
})
</script>

<style scoped lang="scss">
.classplan-view {
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

.clickable-tag {
  cursor: pointer;
  transition: transform 0.15s;

  &:hover {
    transform: scale(1.05);
  }
}

.price {
  font-weight: 600;
  color: var(--danger-500);
}

.matching-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-tertiary);

  .el-icon {
    color: var(--primary-400);
  }
}
</style>
