<template>
  <div class="enrollment-view">
    <div class="page-header">
      <h1>报名管理</h1>
      <el-button v-permission="['enrollment', 'edit']" type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon>
        新增报名
      </el-button>
    </div>

    <!-- Search Bar -->
    <div class="search-bar">
      <el-select v-model="filterStudent" placeholder="学生" clearable filterable style="width: 180px">
        <el-option
          v-for="s in allStudents"
          :key="s.id"
          :label="s.name"
          :value="s.id"
        />
      </el-select>
      <el-select v-model="filterClassPlan" placeholder="开班计划" clearable filterable style="width: 200px">
        <el-option
          v-for="c in allClassPlans"
          :key="c.id"
          :label="c.name"
          :value="c.id"
        />
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px">
        <el-option
          v-for="item in statusOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-select v-model="filterScheduledHours" placeholder="已排课时" clearable style="width: 130px">
        <el-option label="全部" value="" />
        <el-option label="未排课" value="0" />
        <el-option label="已排课" value="gt0" />
      </el-select>
      <el-date-picker
        v-model="filterDateRange"
        type="daterange"
        range-separator="-"
        start-placeholder="报名日期起"
        end-placeholder="报名日期止"
        value-format="YYYY-MM-DD"
        style="width: 240px"
        clearable
      />
      <el-button @click="handleSearch">搜索</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- Table -->
    <el-table :data="enrollments" v-loading="loading" stripe table-layout="fixed">
      <el-table-column label="学生" mid-width="100">
        <template #default="{ row }">
          {{ row.student?.name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="开班计划" mid-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.class_plan?.name || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="enroll_date" label="报名日期" width="110">
        <template #default="{ row }">
          {{ formatDate(row.enroll_date) }}
        </template>
      </el-table-column>
      <el-table-column prop="paid_amount" label="付款金额" width="100" align="right">
        <template #default="{ row }">
          <span class="price">¥{{ Number(row.paid_amount || 0).toFixed(0) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="课时" min-width="160" align="center">
        <template #default="{ row }">
          <el-tooltip content="已用/已排/总课时" placement="top">
            <el-tag
              size="small"
              :type="Number(row.used_hours) + Number(row.scheduled_hours || 0) >= Number(row.purchased_hours) ? 'danger' : 'success'"
              class="clickable-tag"
              @click="showLessonRecords(row)"
            >
              {{ Number(row.used_hours).toFixed(1) }}/{{ Number(row.scheduled_hours || 0).toFixed(1) }}/{{ Number(row.purchased_hours).toFixed(1) }}
            </el-tag>
          </el-tooltip>
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
          {{ formatDateTime(row.created_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button v-permission="['enrollment', 'edit']" link type="primary" size="small" @click="showDialog(row)">编辑</el-button>
          <el-popconfirm title="确定删除该报名记录？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button v-permission="['enrollment', 'delete']" link type="danger" size="small">删除</el-button>
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
      :title="editingItem ? '编辑报名' : '新增报名'"
      width="550px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="学生" prop="student_id">
          <el-select
            v-model="form.student_id"
            placeholder="请选择学生"
            filterable
            style="width: 100%"
            :disabled="!!editingItem"
          >
            <el-option
              v-for="s in allStudents"
              :key="s.id"
              :label="`${s.name} ${s.phone || ''}`"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="开班计划" prop="class_plan_id">
          <el-select
            v-model="form.class_plan_id"
            placeholder="请选择开班计划"
            filterable
            style="width: 100%"
            :disabled="!!editingItem"
            @change="handleClassPlanChange"
          >
            <el-option
              v-for="c in allClassPlans"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <!-- 课程参考信息 -->
        <div v-if="selectedClassPlan?.course" class="course-reference">
          <el-alert type="info" :closable="false" show-icon>
            <template #title>
              <span>课程参考：</span>
              <span class="ref-item">课时单价 <strong>¥{{ selectedClassPlan.course.unit_price }}/小时</strong></span>
            </template>
          </el-alert>
        </div>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="付款金额" prop="paid_amount">
              <el-input-number v-model="form.paid_amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="购买课时" prop="purchased_hours">
              <el-input-number
                v-model="form.purchased_hours"
                :min="0"
                :precision="1"
                :step="0.5"
                style="width: 100%"
                @blur="handlePurchasedHoursBlur"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20" v-if="editingItem">
          <el-col :span="12">
            <el-form-item label="已用课时">
              <el-input :model-value="form.used_hours" disabled style="width: 100%">
                <template #suffix>
                  <span style="color: var(--text-tertiary); font-size: 12px;">由排课消耗</span>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="form.status" style="width: 100%">
                <el-option label="在读" value="active" />
                <el-option label="结业" value="completed" />
                <el-option label="退费" value="refunded" />
                <el-option label="取消" value="cancelled" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注" prop="notes">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 课时记录弹窗 -->
    <el-dialog
      v-model="recordsDialogVisible"
      :title="`课时记录 - ${selectedEnrollment?.student?.name || ''}`"
      width="750px"
    >
      <div v-if="selectedEnrollment" class="enrollment-info">
        <el-descriptions :column="4" border size="small">
          <el-descriptions-item label="学生">{{ selectedEnrollment.student?.name }}</el-descriptions-item>
          <el-descriptions-item label="开班计划">{{ selectedEnrollment.class_plan?.name }}</el-descriptions-item>
          <el-descriptions-item label="已用/购买">
            <el-tag size="small" :type="Number(selectedEnrollment.used_hours) >= Number(selectedEnrollment.purchased_hours) ? 'danger' : 'success'">
              {{ Number(selectedEnrollment.used_hours).toFixed(1) }} / {{ Number(selectedEnrollment.purchased_hours).toFixed(1) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="已排">
            <el-tag size="small" type="primary">{{ Number(selectedEnrollment.scheduled_hours || 0).toFixed(1) }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <el-tabs v-model="recordsActiveTab" @tab-change="handleRecordTabChange">
        <el-tab-pane label="已用" name="used">
          <el-table :data="lessonRecords" v-loading="recordsLoading" stripe size="small" class="records-table">
            <el-table-column prop="record_date" label="日期" width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.created_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="hours" label="课时" width="70" align="center">
              <template #default="{ row }">
                <span class="hours-value">{{ Number(row.hours).toFixed(1) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="class_plan_name" label="班级" min-width="100" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.class_plan_name || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="teacher_name" label="教师" width="90">
              <template #default="{ row }">
                {{ row.teacher_name || '-' }}
              </template>
            </el-table-column>
          </el-table>

          <div class="records-pagination" v-if="recordsTotal > recordsPageSize">
            <el-pagination
              v-model:current-page="recordsPage"
              :page-size="recordsPageSize"
              :total="recordsTotal"
              layout="total, prev, pager, next"
              @current-change="loadLessonRecords"
            />
          </div>

          <el-empty v-if="!recordsLoading && lessonRecords.length === 0" description="暂无课时消耗记录" />
        </el-tab-pane>

        <el-tab-pane label="已排" name="scheduled">
          <el-table :data="scheduledRecords" v-loading="scheduledLoading" stripe size="small" class="records-table">
            <el-table-column label="日期" width="160">
              <template #default="{ row }">
                {{ formatDate(row.schedule_date) }} {{ row.start_time?.slice(0, 5) }}
              </template>
            </el-table-column>
            <el-table-column prop="lesson_hours" label="课时" width="70" align="center">
              <template #default="{ row }">
                <span class="hours-value">{{ Number(row.lesson_hours).toFixed(1) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="class_plan" label="班级" min-width="100" show-overflow-tooltip>
              <template #default="{ row }">
                {{ row.class_plan?.name || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="teacher" label="教师" width="90">
              <template #default="{ row }">
                {{ row.teacher?.name || '-' }}
              </template>
            </el-table-column>
          </el-table>

          <div class="records-pagination" v-if="scheduledTotal > scheduledPageSize">
            <el-pagination
              v-model:current-page="scheduledPage"
              :page-size="scheduledPageSize"
              :total="scheduledTotal"
              layout="total, prev, pager, next"
              @current-change="loadScheduledRecords"
            />
          </div>

          <el-empty v-if="!scheduledLoading && scheduledRecords.length === 0" description="暂无待上课排课" />
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="recordsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  getEnrollments, createEnrollment, updateEnrollment, deleteEnrollment,
  type Enrollment, type EnrollmentCreate
} from '@/api/enrollment'
import { getAllStudents, type Student } from '@/api/student'
import { getAllClassPlans, type ClassPlanBrief } from '@/api/classplan'
import { getLessonRecordsByEnrollment, type LessonRecord } from '@/api/lessonRecord'
import { getSchedules, type Schedule } from '@/api/schedule'
import { getDictItems, type DictItem } from '@/api/dictionary'

// State
const enrollments = ref<Enrollment[]>([])
const allStudents = ref<Student[]>([])
const allClassPlans = ref<ClassPlanBrief[]>([])
const statusOptions = ref<DictItem[]>([])
const loading = ref(false)
const saving = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterStudent = ref<number | undefined>(undefined)
const filterClassPlan = ref<number | undefined>(undefined)
const filterStatus = ref('')
const filterScheduledHours = ref('')  // 已排课时过滤: ''=全部, '0'=未排课, 'gt0'=已排课
const filterDateRange = ref<[string, string] | null>(null)  // 报名日期范围过滤

// Dialog
const dialogVisible = ref(false)
const editingItem = ref<Enrollment | null>(null)
const formRef = ref<FormInstance>()
const form = ref<EnrollmentCreate & { used_hours?: number }>({
  student_id: undefined as unknown as number,
  class_plan_id: undefined as unknown as number,
  paid_amount: 0,
  purchased_hours: 0,
  status: 'active',
  notes: '',
})

const rules: FormRules = {
  student_id: [{ required: true, message: '请选择学生', trigger: 'change' }],
  class_plan_id: [{ required: true, message: '请选择开班计划', trigger: 'change' }],
}

// 课时记录弹窗状态
const recordsDialogVisible = ref(false)
const selectedEnrollment = ref<Enrollment | null>(null)
const recordsActiveTab = ref('used')  // 标签页: 'used' | 'scheduled'

// 已用课时记录
const lessonRecords = ref<LessonRecord[]>([])
const recordsLoading = ref(false)
const recordsPage = ref(1)
const recordsPageSize = 10
const recordsTotal = ref(0)

// 已排课时记录
const scheduledRecords = ref<Schedule[]>([])
const scheduledLoading = ref(false)
const scheduledPage = ref(1)
const scheduledPageSize = 10
const scheduledTotal = ref(0)
const scheduleStatusOptions = ref<DictItem[]>([])

// Computed - 当前选中的开班计划（用于显示课程参考价格）
const selectedClassPlan = computed(() => {
  if (!form.value.class_plan_id) return null
  return allClassPlans.value.find(c => c.id === form.value.class_plan_id) || null
})

// Methods
const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return `${d.toLocaleDateString('zh-CN')} ${d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`
}

// 显示课时记录弹窗
const showLessonRecords = async (enrollment: Enrollment) => {
  selectedEnrollment.value = enrollment
  recordsActiveTab.value = 'used'  // 默认显示已用标签页
  // 重置已用记录
  recordsPage.value = 1
  lessonRecords.value = []
  recordsTotal.value = 0
  // 重置已排记录
  scheduledPage.value = 1
  scheduledRecords.value = []
  scheduledTotal.value = 0

  recordsDialogVisible.value = true
  await loadLessonRecords()
}

// 加载课时消耗记录
const loadLessonRecords = async () => {
  if (!selectedEnrollment.value) return
  recordsLoading.value = true
  try {
    const res = await getLessonRecordsByEnrollment(selectedEnrollment.value.id, {
      page: recordsPage.value,
      page_size: recordsPageSize,
    })
    lessonRecords.value = res.data?.items || []
    recordsTotal.value = res.data?.total || 0
  } catch (e) {
    console.error('加载课时记录失败', e)
  } finally {
    recordsLoading.value = false
  }
}

// 加载已排课记录（只加载未完成的）
const loadScheduledRecords = async () => {
  if (!selectedEnrollment.value) return
  scheduledLoading.value = true
  try {
    const res = await getSchedules({
      class_plan_id: selectedEnrollment.value.class_plan_id,
      status: 'scheduled',  // 只显示待上课的排课
      page: scheduledPage.value,
      page_size: scheduledPageSize,
    })
    scheduledRecords.value = res.data?.items || []
    scheduledTotal.value = res.data?.total || 0
  } catch (e) {
    console.error('加载排课记录失败', e)
  } finally {
    scheduledLoading.value = false
  }
}

// 标签页切换处理
const handleRecordTabChange = (tabName: string | number) => {
  if (tabName === 'scheduled' && scheduledRecords.value.length === 0) {
    scheduledPage.value = 1
    loadScheduledRecords()
  }
}

const getStatusLabel = (status: string) => {
  return statusOptions.value.find(i => i.value === status)?.label || status
}

const getStatusType = (status: string) => {
  // 从数据字典取颜色（color字段存储el-tag的type值）
  return statusOptions.value.find(i => i.value === status)?.color || 'info'
}

const loadOptions = async () => {
  try {
    const [studentsRes, classPlansRes, statusRes, scheduleStatusRes] = await Promise.all([
      getAllStudents(false),
      getAllClassPlans(false),
      getDictItems('enrollment_status'),
      getDictItems('schedule_status'),
    ])
    allStudents.value = studentsRes || []
    allClassPlans.value = classPlansRes || []
    statusOptions.value = statusRes || []
    scheduleStatusOptions.value = scheduleStatusRes || []
  } catch {
    // ignore
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getEnrollments({
      page: currentPage.value,
      page_size: pageSize.value,
      student_id: filterStudent.value,
      class_plan_id: filterClassPlan.value,
      status: filterStatus.value || undefined,
      enroll_date_from: filterDateRange.value?.[0],
      enroll_date_to: filterDateRange.value?.[1],
    })
    let items = res.data?.items || []

    // 前端过滤：已排课时
    if (filterScheduledHours.value) {
      if (filterScheduledHours.value === '0') {
        items = items.filter((e: Enrollment) => !e.scheduled_hours || Number(e.scheduled_hours) === 0)
      } else if (filterScheduledHours.value === 'gt0') {
        items = items.filter((e: Enrollment) => Number(e.scheduled_hours) > 0)
      }
    }

    enrollments.value = items
    total.value = items.length  // 注意：过滤后总数是前端过滤后的数量
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadData()
}

const handleReset = () => {
  filterStudent.value = undefined
  filterClassPlan.value = undefined
  filterStatus.value = ''
  filterScheduledHours.value = ''
  filterDateRange.value = null
  currentPage.value = 1
  loadData()
}

// 选择开班计划时，自动填充课时单价作为默认值
const handleClassPlanChange = (classPlanId: number) => {
  const classPlan = allClassPlans.value.find(c => c.id === classPlanId)
  if (classPlan?.course) {
    // 价格和课时需要在开班计划中设置，这里不再自动填充
    // 课时单价可以从课程产品获取，用于计算参考
    form.value.paid_amount = 0
    form.value.purchased_hours = 0
  }
}

// 课时输入失焦时，根据开班单价自动计算付款金额
const handlePurchasedHoursBlur = () => {
  if (selectedClassPlan.value?.course?.unit_price && form.value.purchased_hours) {
    const unitPrice = Number(selectedClassPlan.value.course.unit_price)
    const hours = Number(form.value.purchased_hours)
    form.value.paid_amount = Math.round(unitPrice * hours * 100) / 100
  }
}

const showDialog = (item?: Enrollment) => {
  editingItem.value = item || null
  if (item) {
    form.value = {
      student_id: item.student_id,
      class_plan_id: item.class_plan_id,
      paid_amount: Number(item.paid_amount),
      purchased_hours: Number(item.purchased_hours),
      used_hours: Number(item.used_hours),
      status: item.status,
      notes: item.notes || '',
    }
  } else {
    form.value = {
      student_id: undefined as unknown as number,
      class_plan_id: undefined as unknown as number,
      paid_amount: 0,
      purchased_hours: 0,
      status: 'active',
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
      // 注意：used_hours由排课消耗自动计算，不应手动更新
      await updateEnrollment(editingItem.value.id, {
        paid_amount: form.value.paid_amount,
        purchased_hours: form.value.purchased_hours,
        status: form.value.status,
        notes: form.value.notes,
      })
      ElMessage.success('更新成功')
    } else {
      await createEnrollment(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteEnrollment(id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => {
  loadOptions()
  loadData()
})
</script>

<style scoped lang="scss">
.enrollment-view {
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
  color: var(--danger-500);
}

.course-reference {
  margin-bottom: 18px;

  :deep(.el-alert__title) {
    display: flex;
    align-items: center;
    gap: 16px;
    font-size: 13px;
  }

  .ref-item {
    color: var(--text-secondary);

    strong {
      color: var(--primary-600);
      margin-left: 4px;
    }
  }
}

// 可点击的Tag样式
.clickable-tag {
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    transform: scale(1.05);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }
}

// 课时记录弹窗样式
.enrollment-info {
  margin-bottom: 16px;
}

.records-table {
  margin-top: 12px;
}

.hours-value {
  font-weight: 600;
  color: var(--primary-600);
}

.records-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.text-warning {
  color: var(--warning-500);
  font-weight: 600;
}
</style>
