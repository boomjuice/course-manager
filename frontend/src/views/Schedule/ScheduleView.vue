<template>
  <div class="schedule-view">
    <div class="page-header">
      <div class="header-left">
        <h1>课表管理</h1>
        <!-- 日期导航 -->
        <div class="date-nav">
          <el-button-group>
            <el-button @click="navigateCalendar('prev')">
              <el-icon><ArrowLeft /></el-icon>
            </el-button>
            <el-button @click="navigateCalendar('today')">今天</el-button>
            <el-button @click="navigateCalendar('next')">
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </el-button-group>
          <span class="current-date">{{ currentDateRange }}</span>
        </div>
        <!-- 视图切换 -->
        <el-radio-group v-model="currentView" size="small" @change="changeView">
          <el-radio-button value="day">日</el-radio-button>
          <el-radio-button value="week">周</el-radio-button>
          <el-radio-button value="month">月</el-radio-button>
        </el-radio-group>
      </div>
      <div class="header-actions">
        <el-select v-model="filterClassPlan" placeholder="筛选班级" clearable filterable style="width: 180px">
          <el-option
            v-for="c in allClassPlans"
            :key="c.id"
            :label="c.name"
            :value="c.id"
          />
        </el-select>
        <el-select v-model="filterTeacher" placeholder="筛选教师" clearable filterable style="width: 150px">
          <el-option
            v-for="t in allTeachers"
            :key="t.id"
            :label="t.name"
            :value="t.id"
          />
        </el-select>
        <el-button v-permission="['schedule', 'edit']" type="primary" @click="showDialog()">
          <el-icon><Plus /></el-icon>
          新增排课
        </el-button>
        <el-button v-permission="['schedule', 'edit']" type="success" @click="showBatchDialog()">
          <el-icon><CalendarIcon /></el-icon>
          批量排课
        </el-button>
      </div>
    </div>

    <!-- Calendar Container -->
    <div class="calendar-container" v-loading="loading">
      <div ref="calendarRef" class="calendar"></div>
    </div>

    <!-- Schedule Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingItem ? '编辑排课' : '新增排课'"
      width="550px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="班级" prop="class_plan_id">
          <el-select
            v-model="form.class_plan_id"
            placeholder="请选择班级"
            filterable
            style="width: 100%"
            :disabled="!!editingItem"
          >
            <el-option
              v-for="c in allClassPlans"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="授课教师" prop="teacher_id">
              <el-select v-model="form.teacher_id" placeholder="教师" filterable clearable style="width: 100%">
                <el-option
                  v-for="t in allTeachers"
                  :key="t.id"
                  :label="t.name"
                  :value="t.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="教室" prop="classroom_id">
              <el-select v-model="form.classroom_id" placeholder="教室" filterable clearable style="width: 100%">
                <el-option
                  v-for="r in allClassrooms"
                  :key="r.id"
                  :label="r.name"
                  :value="r.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="上课日期" prop="schedule_date">
          <el-date-picker
            v-model="form.schedule_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间" prop="start_time">
              <el-time-picker
                v-model="form.start_time"
                placeholder="开始"
                format="HH:mm"
                value-format="HH:mm:ss"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间" prop="end_time">
              <el-time-picker
                v-model="form.end_time"
                placeholder="结束"
                format="HH:mm"
                value-format="HH:mm:ss"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="课时数" prop="lesson_hours">
              <el-input-number v-model="form.lesson_hours" :min="0.5" :max="10" :step="0.5" :precision="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="editingItem">
            <el-form-item label="状态" prop="status">
              <el-select v-model="form.status" style="width: 100%">
                <el-option label="已排课" value="scheduled" />
                <el-option label="已完成" value="completed" />
                <el-option label="已取消" value="cancelled" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="课程标题" prop="title">
          <el-input v-model="form.title" placeholder="可选，不填默认显示班级名称" />
        </el-form-item>
        <el-form-item label="备注" prop="notes">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-tooltip
          v-if="editingItem"
          :content="editingItem?.raw?.status === 'completed' ? '已完成的排课不可删除' : ''"
          :disabled="editingItem?.raw?.status !== 'completed'"
          placement="top"
        >
          <el-button
            v-permission="['schedule', 'delete']"
            type="danger"
            :disabled="editingItem?.raw?.status === 'completed'"
            @click="handleDelete"
          >删除</el-button>
        </el-tooltip>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- Schedule Detail Dialog - 课程详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="课程详情"
      width="500px"
    >
      <div v-if="detailEvent" class="schedule-detail">
        <div class="detail-header">
          <h3>{{ detailEvent.title || '课程' }}</h3>
          <el-tag :type="getStatusType(detailEvent.raw?.status)">
            {{ getStatusLabel(detailEvent.raw?.status) }}
          </el-tag>
        </div>

        <el-descriptions :column="1" border>
          <el-descriptions-item label="班级">
            {{ detailEvent.raw?.class_plan_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="授课教师">
            {{ detailEvent.raw?.teacher_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="上课教室">
            {{ detailEvent.raw?.classroom_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="上课时间">
            {{ formatEventTime(detailEvent) }}
          </el-descriptions-item>
          <el-descriptions-item label="课时数">
            {{ detailEvent.raw?.lesson_hours || 0 }} 课时
          </el-descriptions-item>
          <el-descriptions-item v-if="detailEvent.raw?.notes" label="备注">
            {{ detailEvent.raw.notes }}
          </el-descriptions-item>
          <el-descriptions-item v-if="detailEvent.raw?.batch_no" label="批次号">
            <div class="batch-info">
              <code>{{ detailEvent.raw.batch_no }}</code>
              <el-button type="primary" link size="small" @click="showBatchOperationDialog()">
                <el-icon><Operation /></el-icon>
                批量操作
              </el-button>
            </div>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 学生名单 & 出勤管理 -->
        <div class="student-list-section">
          <div class="section-header">
            <span>学生出勤</span>
            <el-tag size="small" type="info">{{ scheduleAttendances.length }} 人</el-tag>
          </div>
          <div v-loading="loadingStudents" class="student-list">
            <template v-if="scheduleAttendances.length > 0">
              <div v-for="item in scheduleAttendances" :key="item.enrollment_id" class="student-item">
                <span class="student-name">{{ item.student_name || '-' }}</span>
                <el-radio-group
                  v-model="item.status"
                  size="small"
                  @change="handleAttendanceChange(item)"
                >
                  <el-radio-button value="normal">正常</el-radio-button>
                  <el-radio-button value="leave">请假</el-radio-button>
                  <el-radio-button value="absent">缺勤</el-radio-button>
                </el-radio-group>
                <el-input
                  v-if="item.status === 'leave'"
                  v-model="item.leave_reason"
                  size="small"
                  placeholder="请假原因"
                  style="width: 100px; margin-left: 8px"
                  @blur="handleAttendanceChange(item)"
                />
              </div>
            </template>
            <el-empty v-else description="暂无学生报名" :image-size="60" />
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button v-permission="['schedule', 'edit']" type="primary" @click="editFromDetail">编辑排课</el-button>
      </template>
    </el-dialog>

    <!-- Batch Schedule Dialog -->
    <el-dialog
      v-model="batchDialogVisible"
      title="批量排课"
      width="700px"
    >
      <el-form ref="batchFormRef" :model="batchForm" :rules="batchRules" label-width="100px">
        <el-form-item label="班级" prop="class_plan_id">
          <el-select v-model="batchForm.class_plan_id" placeholder="请选择班级" filterable style="width: 100%">
            <el-option v-for="c in allClassPlans" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="授课教师" prop="teacher_id">
              <el-select v-model="batchForm.teacher_id" placeholder="教师" filterable clearable style="width: 100%">
                <el-option v-for="t in allTeachers" :key="t.id" :label="t.name" :value="t.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="教室" prop="classroom_id">
              <el-select v-model="batchForm.classroom_id" placeholder="教室" filterable clearable style="width: 100%">
                <el-option v-for="r in allClassrooms" :key="r.id" :label="r.name" :value="r.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <!-- 多日期范围配置 -->
        <el-form-item label="日期范围" prop="dateRanges" class="date-ranges-form-item">
          <div class="date-ranges-container">
            <div class="date-ranges-header">
              <span class="header-title">配置上课日期范围</span>
              <el-button type="primary" link size="small" @click="addDateRange">
                <el-icon><Plus /></el-icon>
                添加日期范围
              </el-button>
            </div>
            <div class="date-ranges-list">
              <div v-for="(item, index) in batchForm.dateRanges" :key="index" class="date-range-item">
                <el-date-picker
                  v-model="item.range"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 300px"
                />
                <el-button
                  type="danger"
                  link
                  @click="removeDateRange(index)"
                  :disabled="batchForm.dateRanges.length <= 1"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="date-ranges-hint">
              提示：可以添加多个不连续的日期范围，例如寒假班+开学前冲刺班
            </div>
          </div>
        </el-form-item>

        <!-- 每周上课时间段配置 -->
        <el-form-item label="上课时间" prop="timeSlots" class="time-slots-form-item">
          <div class="time-slots-container">
            <div class="time-slots-header">
              <span class="header-title">配置上课时间段</span>
              <el-button type="primary" link size="small" @click="addTimeSlot">
                <el-icon><Plus /></el-icon>
                添加时间段
              </el-button>
            </div>
            <div class="time-slots-list">
              <div v-for="(slot, index) in batchForm.timeSlots" :key="index" class="time-slot-item">
                <div class="weekday-select">
                  <el-select
                    v-model="slot.weekdays"
                    multiple
                    placeholder="选择周几"
                    style="width: 200px"
                    collapse-tags
                    collapse-tags-tooltip
                  >
                    <el-option
                      v-for="day in weekdayOptions"
                      :key="day.value"
                      :label="day.label"
                      :value="day.value"
                    />
                  </el-select>
                  <el-button type="primary" link size="small" @click="toggleAllWeekdaysForSlot(index)">
                    {{ slot.weekdays.length === 7 ? '清空' : '全选' }}
                  </el-button>
                </div>
                <el-time-picker
                  v-model="slot.start_time"
                  placeholder="开始"
                  format="HH:mm"
                  value-format="HH:mm:ss"
                  style="width: 120px"
                />
                <span class="time-separator">-</span>
                <el-time-picker
                  v-model="slot.end_time"
                  placeholder="结束"
                  format="HH:mm"
                  value-format="HH:mm:ss"
                  style="width: 120px"
                />
                <el-button
                  type="danger"
                  link
                  @click="removeTimeSlot(index)"
                  :disabled="batchForm.timeSlots.length <= 1"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="time-slots-hint">
              提示：可以为不同的上课日设置不同的时间段，例如周一三五上午、周二四下午
            </div>
          </div>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="课时数" prop="lesson_hours">
              <el-input-number v-model="batchForm.lesson_hours" :min="0.5" :max="10" :step="0.5" :precision="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="课程标题" prop="title">
          <el-input v-model="batchForm.title" placeholder="可选，不填默认显示班级名称" />
        </el-form-item>
        <el-form-item label="备注" prop="notes">
          <el-input v-model="batchForm.notes" type="textarea" :rows="2" placeholder="备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchSave" :loading="batchSaving">
          批量创建
        </el-button>
      </template>
    </el-dialog>

    <!-- Batch Operation Dialog - 批量操作弹窗（从详情进入） -->
    <el-dialog
      v-model="batchOperationDialogVisible"
      title="批量操作"
      width="750px"
    >
      <div class="batch-operation-content">
        <!-- 批次信息 -->
        <div class="batch-header">
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item label="批次号">
              <code>{{ batchOperationBatchNo }}</code>
            </el-descriptions-item>
            <el-descriptions-item label="班级">
              {{ batchSchedules[0]?.class_plan?.name || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="日期范围">
              {{ batchDateRange }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 批次排课列表（放上面，支持多选） -->
        <div class="batch-schedule-list">
          <div class="list-header">
            <span>选择要操作的排课</span>
            <el-tag size="small" type="info">已选 {{ selectedScheduleIds.length }} / {{ batchSchedules.length }} 条</el-tag>
          </div>
          <el-table
            ref="batchTableRef"
            :data="batchSchedules"
            max-height="280"
            size="small"
            v-loading="loadingBatchSchedules"
            @selection-change="handleBatchSelectionChange"
            row-key="id"
          >
            <el-table-column type="selection" width="45" :selectable="checkBatchSelectable" />
            <el-table-column prop="schedule_date" label="日期" width="110" />
            <el-table-column label="时间" width="120">
              <template #default="{ row }">
                {{ row.start_time?.slice(0, 5) }} - {{ row.end_time?.slice(0, 5) }}
              </template>
            </el-table-column>
            <el-table-column label="教师" min-width="90">
              <template #default="{ row }">
                {{ row.teacher?.name || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="教室" min-width="90">
              <template #default="{ row }">
                {{ row.classroom?.name || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="batchSchedules.some(s => s.status === 'completed')" class="batch-tip">
            <el-text type="warning" size="small">
              <el-icon><Warning /></el-icon>
              已完成的排课无法更新或删除
            </el-text>
          </div>
        </div>

        <!-- 操作区域（放下面） -->
        <div class="batch-actions">
          <el-tabs v-model="batchOperationTab">
            <!-- 批量更新 -->
            <el-tab-pane label="批量更新" name="update">
              <el-form label-width="100px" style="margin-top: 12px">
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="更换教师">
                      <el-select v-model="batchUpdateForm.teacher_id" placeholder="不更改" filterable clearable style="width: 100%">
                        <el-option v-for="t in allTeachers" :key="t.id" :label="t.name" :value="t.id" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="更换教室">
                      <el-select v-model="batchUpdateForm.classroom_id" placeholder="不更改" filterable clearable style="width: 100%">
                        <el-option v-for="r in allClassrooms" :key="r.id" :label="r.name" :value="r.id" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-form-item label="更新备注">
                  <el-input v-model="batchUpdateForm.notes" placeholder="不填则不更改" />
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- 批量删除 -->
            <el-tab-pane label="批量删除" name="delete">
              <el-alert
                type="warning"
                :closable="false"
                show-icon
                style="margin-top: 12px"
              >
                <template #title>
                  删除操作不可恢复，请确认已选择正确的排课记录！
                </template>
              </el-alert>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
      <template #footer>
        <div class="batch-dialog-footer">
          <span class="selection-info">
            已选择 <strong>{{ selectedScheduleIds.length }}</strong> 条排课
          </span>
          <div class="footer-buttons">
            <el-button @click="batchOperationDialogVisible = false">取消</el-button>
            <el-button
              v-if="batchOperationTab === 'update'"
              type="primary"
              @click="handleBatchUpdate"
              :loading="batchUpdating"
              :disabled="selectedScheduleIds.length === 0"
            >
              确认更新
            </el-button>
            <el-button
              v-else
              type="danger"
              @click="handleBatchDeleteFromDialog"
              :loading="batchDeleting"
              :disabled="selectedScheduleIds.length === 0"
            >
              <el-icon><Delete /></el-icon>
              确认删除
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick, onBeforeUnmount } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { Plus, Calendar as CalendarIcon, ArrowLeft, ArrowRight, Delete, Operation, Warning } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
// @ts-ignore - TOAST UI Calendar lacks proper exports typings
import ToastCalendar from '@toast-ui/calendar'
import '@toast-ui/calendar/dist/toastui-calendar.min.css'
import {
  getCalendarEvents, createSchedule, updateSchedule, deleteSchedule,
  batchCreateSchedule, batchPreviewSchedule, batchUpdateSchedules, batchDeleteSchedules,
  getBatchSchedules, checkScheduleConflicts,
  type CalendarEvent, type ScheduleCreate, type ScheduleBatchCreate,
  type ScheduleBatchUpdate, type Schedule, type BatchConflictItem
} from '@/api/schedule'
import { getEnrollments, getClassPlanHoursSummary, type Enrollment, type ClassPlanHoursSummary, type StudentHoursDetail } from '@/api/enrollment'
import { getAllClassPlans, type ClassPlanBrief } from '@/api/classplan'
import { getAllTeachers, type Teacher } from '@/api/teacher'
import { getAllClassrooms, type Classroom } from '@/api/campus'
import { getScheduleAttendances, markAttendance, type ScheduleAttendanceItem } from '@/api/attendance'
import { getDictItems, type DictItem } from '@/api/dictionary'

// State
const loading = ref(false)
const saving = ref(false)
const calendarRef = ref<HTMLElement | null>(null)
let calendarInstance: ToastCalendar | null = null

// 视图控制
const currentView = ref<'day' | 'week' | 'month'>('week')
const currentDateRangeStart = ref<Date>(new Date())
const currentDateRangeEnd = ref<Date>(new Date())

// 当前日期范围显示
const currentDateRange = computed(() => {
  const start = currentDateRangeStart.value
  const end = currentDateRangeEnd.value
  const formatDate = (d: Date) => `${d.getMonth() + 1}月${d.getDate()}日`

  if (currentView.value === 'day') {
    return `${start.getFullYear()}年${formatDate(start)}`
  } else if (currentView.value === 'week') {
    return `${start.getFullYear()}年${formatDate(start)} - ${formatDate(end)}`
  } else {
    // 月视图：用中间日期确定当前显示的是哪个月（因为范围可能跨月）
    const midDate = new Date((start.getTime() + end.getTime()) / 2)
    return `${midDate.getFullYear()}年${midDate.getMonth() + 1}月`
  }
})

// Filters
const filterClassPlan = ref<number | undefined>(undefined)
const filterTeacher = ref<number | undefined>(undefined)

// Options data
const allClassPlans = ref<ClassPlanBrief[]>([])
const allTeachers = ref<Teacher[]>([])
const allClassrooms = ref<Classroom[]>([])
const scheduleStatusOptions = ref<DictItem[]>([])

// Dialog
const dialogVisible = ref(false)
const editingItem = ref<CalendarEvent | null>(null)
const formRef = ref<FormInstance>()

// Detail Dialog - 课程详情弹窗
const detailDialogVisible = ref(false)
const detailEvent = ref<CalendarEvent | null>(null)
const detailStudents = ref<Enrollment[]>([])
const loadingStudents = ref(false)
const scheduleAttendances = ref<ScheduleAttendanceItem[]>([])
const form = ref<ScheduleCreate & { status?: string }>({
  class_plan_id: undefined,
  teacher_id: undefined,
  classroom_id: undefined,
  schedule_date: '',
  start_time: '',
  end_time: '',
  lesson_hours: 2,
  title: '',
  notes: '',
})

const rules: FormRules = {
  class_plan_id: [{ required: true, message: '请选择班级', trigger: 'change' }],
  schedule_date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
}

// Batch Dialog - 时间段类型
interface TimeSlot {
  weekdays: number[]  // 选中的周几
  start_time: string
  end_time: string
}

interface DateRangeItem {
  range: [string, string] | null
}

interface BatchFormType {
  class_plan_id: number | undefined
  teacher_id?: number
  classroom_id?: number
  dateRanges: DateRangeItem[]  // 多个日期范围
  timeSlots: TimeSlot[]  // 多个时间段
  lesson_hours: number
  title: string
  notes: string
}

const batchDialogVisible = ref(false)
const batchSaving = ref(false)
const batchFormRef = ref<FormInstance>()
const batchForm = ref<BatchFormType>({
  class_plan_id: undefined,
  teacher_id: undefined,
  classroom_id: undefined,
  dateRanges: [{ range: null }],
  timeSlots: [{ weekdays: [], start_time: '09:00:00', end_time: '11:00:00' }],
  lesson_hours: 2,
  title: '',
  notes: '',
})

// 周几选项
const weekdayOptions = [
  { value: 0, label: '周一' },
  { value: 1, label: '周二' },
  { value: 2, label: '周三' },
  { value: 3, label: '周四' },
  { value: 4, label: '周五' },
  { value: 5, label: '周六' },
  { value: 6, label: '周日' },
]

// 添加日期范围
const addDateRange = () => {
  batchForm.value.dateRanges.push({ range: null })
}

// 删除日期范围
const removeDateRange = (index: number) => {
  if (batchForm.value.dateRanges.length > 1) {
    batchForm.value.dateRanges.splice(index, 1)
  }
}

// 添加时间段
const addTimeSlot = () => {
  batchForm.value.timeSlots.push({
    weekdays: [],
    start_time: '14:00:00',
    end_time: '16:00:00',
  })
}

// 删除时间段
const removeTimeSlot = (index: number) => {
  if (batchForm.value.timeSlots.length > 1) {
    batchForm.value.timeSlots.splice(index, 1)
  }
}

// 为某个时间段全选/清空周几
const toggleAllWeekdaysForSlot = (slotIndex: number) => {
  const slot = batchForm.value.timeSlots[slotIndex]
  if (!slot) return

  if (slot.weekdays.length === 7) {
    // 已经全选了，清空
    slot.weekdays = []
  } else {
    // 全选
    slot.weekdays = [0, 1, 2, 3, 4, 5, 6]
  }
}

// 自定义校验时间段
const validateTimeSlots = (_rule: any, _value: any, callback: any) => {
  const slots = batchForm.value.timeSlots
  // 必须至少选择一个周几
  const hasWeekday = slots.some(slot => slot.weekdays.length > 0)
  if (!hasWeekday) {
    callback(new Error('请至少选择一个上课日'))
    return
  }
  // 每个有选中周几的时间段都要有完整的时间
  for (const slot of slots) {
    if (slot.weekdays.length > 0 && (!slot.start_time || !slot.end_time)) {
      callback(new Error('请为每个时间段设置开始和结束时间'))
      return
    }
  }
  callback()
}

// 自定义校验日期范围
const validateDateRanges = (_rule: any, _value: any, callback: any) => {
  const ranges = batchForm.value.dateRanges
  // 必须至少有一个有效的日期范围
  const hasValidRange = ranges.some(r => r.range && r.range[0] && r.range[1])
  if (!hasValidRange) {
    callback(new Error('请至少设置一个日期范围'))
    return
  }
  callback()
}

const batchRules: FormRules = {
  class_plan_id: [{ required: true, message: '请选择班级', trigger: 'change' }],
  dateRanges: [{ validator: validateDateRanges, trigger: 'change' }],
  timeSlots: [{ validator: validateTimeSlots, trigger: 'change' }],
}

// Batch Delete Dialog
const batchDeleting = ref(false)
const lastBatchNo = ref('')  // 记录上次批量创建返回的批次号

// Batch Operation Dialog - 批量操作弹窗（从详情进入）
const batchOperationDialogVisible = ref(false)
const batchOperationBatchNo = ref('')
const batchOperationTab = ref<'update' | 'delete'>('update')
const batchSchedules = ref<Schedule[]>([])
const loadingBatchSchedules = ref(false)
const batchUpdating = ref(false)
const batchTableRef = ref<any>(null)  // el-table ref
const selectedScheduleIds = ref<number[]>([])  // 选中的排课ID列表

// 批量更新表单
interface BatchUpdateFormType {
  teacher_id?: number
  classroom_id?: number
  notes: string
}

const batchUpdateForm = ref<BatchUpdateFormType>({
  teacher_id: undefined,
  classroom_id: undefined,
  notes: '',
})

// 处理表格选择变化
const handleBatchSelectionChange = (selection: Schedule[]) => {
  selectedScheduleIds.value = selection.map(s => s.id)
}

// 判断批量操作表格行是否可选（已完成的排课不可选）
const checkBatchSelectable = (row: Schedule) => {
  return row.status !== 'completed'
}

// 批次日期范围（计算属性）
const batchDateRange = computed(() => {
  if (batchSchedules.value.length === 0) return '-'
  const dates = batchSchedules.value.map(s => s.schedule_date).sort()
  return `${dates[0]} ~ ${dates[dates.length - 1]}`
})

// Methods
const loadOptions = async () => {
  try {
    const [classPlansRes, teachersRes, classroomsRes, statusRes] = await Promise.all([
      getAllClassPlans(false),
      getAllTeachers(false),
      getAllClassrooms(),
      getDictItems('schedule_status'),
    ])
    allClassPlans.value = classPlansRes || []
    allTeachers.value = teachersRes || []
    allClassrooms.value = classroomsRes || []
    scheduleStatusOptions.value = statusRes || []
  } catch {
    // ignore
  }
}

const loadCalendarEvents = async () => {
  if (!calendarInstance || !isMounted) return

  loading.value = true
  try {
    const range = calendarInstance.getDateRangeStart()
    const rangeEnd = calendarInstance.getDateRangeEnd()

    const startDate = range.toDate().toISOString().split('T')[0]
    const endDate = rangeEnd.toDate().toISOString().split('T')[0]

    const res = await getCalendarEvents({
      start_date: startDate,
      end_date: endDate,
      class_plan_id: filterClassPlan.value,
      teacher_id: filterTeacher.value,
    })

    // Check again after async operation
    if (!calendarInstance || !isMounted) return

    calendarInstance.clear()
    calendarInstance.createEvents((res || []).map(e => ({
      ...e,
      start: new Date(e.start),
      end: new Date(e.end),
    })))
  } finally {
    loading.value = false
  }
}

// 更新当前日期范围显示
const updateDateRange = () => {
  if (!calendarInstance) return
  currentDateRangeStart.value = calendarInstance.getDateRangeStart().toDate()
  currentDateRangeEnd.value = calendarInstance.getDateRangeEnd().toDate()
}

// 日历导航：上一页/今天/下一页
// 注意：月视图用prev()/next()可能跳月不准确，需要手动计算日期
const navigateCalendar = (direction: 'prev' | 'today' | 'next') => {
  if (!calendarInstance) return

  if (direction === 'today') {
    calendarInstance.today()
  } else if (currentView.value === 'month') {
    // 月视图：手动计算上/下月的1号，避免TOAST UI Calendar的SB导航bug
    // getDateRangeStart()返回的是日历视图起始日期（可能是上月末），需要取中间日期来确定当前显示月份
    const rangeStart = calendarInstance.getDateRangeStart().toDate()
    const rangeEnd = calendarInstance.getDateRangeEnd().toDate()
    // 取中间日期来确定当前显示的是哪个月
    const midDate = new Date((rangeStart.getTime() + rangeEnd.getTime()) / 2)
    const newDate = new Date(midDate.getFullYear(), midDate.getMonth() + (direction === 'prev' ? -1 : 1), 15)
    calendarInstance.setDate(newDate)
  } else {
    // 周/日视图：使用内置方法
    if (direction === 'prev') {
      calendarInstance.prev()
    } else {
      calendarInstance.next()
    }
  }

  updateDateRange()
  loadCalendarEvents()
}

// 切换视图：日/周/月
const changeView = (view: 'day' | 'week' | 'month') => {
  if (!calendarInstance) return
  calendarInstance.changeView(view)
  updateDateRange()
  loadCalendarEvents()
}

const initCalendar = () => {
  if (!calendarRef.value) return

  calendarInstance = new ToastCalendar(calendarRef.value, {
    defaultView: 'week',
    usageStatistics: false,
    week: {
      startDayOfWeek: 1, // Monday
      taskView: false,
      eventView: ['time'],
      hourStart: 7,
      hourEnd: 22,
    },
    month: {
      startDayOfWeek: 1,
    },
    template: {
      // 时间轴显示24小时制，不要洋人的am/pm
      timegridDisplayPrimaryTime({ time }: { time: Date }) {
        const hours = time.getHours().toString().padStart(2, '0')
        return `${hours}:00`
      },
      // 月视图日期格头模板 - 只显示日期数字，不要完整的YYYY-MM-DD
      monthGridHeader(model: any) {
        const date = parseInt(model.date.split('-')[2], 10)
        const isToday = model.isToday
        const isOtherMonth = model.isOtherMonth
        // 今天高亮，非本月日期灰色
        let className = ''
        if (isToday) className = 'today'
        else if (isOtherMonth) className = 'other-month'
        return `<span class="${className}">${date}</span>`
      },
      // 月视图的事件显示模板
      monthDayName(model: any) {
        return model.label
      },
      time(event: any) {
        const title = event.title || '课程'
        const teacher = event.attendees?.[0] || ''
        const location = event.location || ''
        const studentCount = event.raw?.student_count ?? 0
        const leaveCount = event.raw?.leave_count ?? 0
        const absentCount = event.raw?.absent_count ?? 0
        const classPlanName = event.raw?.class_plan_name || ''
        const status = event.raw?.status || 'scheduled'

        // 状态标签配置
        const statusConfig: Record<string, { label: string; class: string }> = {
          scheduled: { label: '待上课', class: 'status-scheduled' },
          completed: { label: '已完成', class: 'status-completed' },
          cancelled: { label: '已取消', class: 'status-cancelled' },
        }
        const defaultStatus = { label: '待上课', class: 'status-scheduled' }
        const statusInfo = statusConfig[status] ?? defaultStatus

        // 格式化时间：从event.start和event.end获取
        let timeStr = ''
        if (event.start && event.end) {
          const startDate = new Date(event.start)
          const endDate = new Date(event.end)
          const formatTime = (d: Date) => `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
          timeStr = `${formatTime(startDate)}-${formatTime(endDate)}`
        }

        // 月视图显示简洁信息：时间 + 教师 + 状态图标
        if (currentView.value === 'month') {
          const statusIcon = status === 'completed' ? '✓' : status === 'cancelled' ? '✗' : ''
          return `<span class="month-event ${statusInfo.class}">${statusIcon}${timeStr} ${teacher || title}</span>`
        }

        // 构建出勤统计显示：默认显示人数，有请假缺勤时显示详情
        let attendanceStr = `${studentCount}人`
        if (leaveCount > 0 || absentCount > 0) {
          const details = []
          if (leaveCount > 0) details.push(`<span class="leave-text">${leaveCount}请假</span>`)
          if (absentCount > 0) details.push(`<span class="absent-text">${absentCount}缺勤</span>`)
          attendanceStr = `${studentCount}人(${details.join('，')})`
        }

        // 周/日视图：构建详细卡片内容
        let html = `<div class="schedule-card">`
        // 顶部：时间 + 状态标签
        html += `<div class="schedule-header">`
        if (timeStr) html += `<span class="schedule-time">${timeStr}</span>`
        html += `<span class="schedule-status ${statusInfo.class}">${statusInfo.label}</span>`
        html += `</div>`
        html += `<div class="schedule-title">${title}</div>`
        // 如果标题和班级名称不同，显示班级名称
        if (classPlanName && classPlanName !== title) {
          html += `<div class="schedule-class">${classPlanName}</div>`
        }
        html += `<div class="schedule-info">`
        if (teacher) html += `<div class="info-row"><i class="info-icon teacher"></i>${teacher}</div>`
        if (location) html += `<div class="info-row"><i class="info-icon room"></i>${location}</div>`
        html += `<div class="info-row"><i class="info-icon student"></i>${attendanceStr}</div>`
        html += `</div></div>`
        return html
      },
      // 月视图全天事件模板（月视图里的课程会用这个）
      allday(event: any) {
        const title = event.title || '课程'
        let timeStr = ''
        if (event.start && event.end) {
          const startDate = new Date(event.start)
          const endDate = new Date(event.end)
          const formatTime = (d: Date) => `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
          timeStr = `${formatTime(startDate)}-${formatTime(endDate)}`
        }
        return `<span class="month-event">${timeStr ? timeStr + ' ' : ''}${title}</span>`
      },
    },
    calendars: allClassPlans.value.map((cp, idx) => ({
      id: String(cp.id),
      name: cp.name,
      backgroundColor: getCalendarColor(idx),
      borderColor: getCalendarColor(idx),
    })),
  })

  // Event handlers - 点击事件显示详情弹窗
  // 注意：TOAST UI Calendar的clickEvent在某些情况下不触发，所以用DOM事件作为主要方案
  calendarRef.value?.addEventListener('click', (e: MouseEvent) => {
    const target = e.target as HTMLElement
    // 支持周视图(.toastui-calendar-event-time)和月视图(.toastui-calendar-weekday-event, .toastui-calendar-month-event)
    const eventEl = target.closest('.toastui-calendar-event-time, .toastui-calendar-weekday-event-block, .toastui-calendar-event')
    if (eventEl) {
      // 从data属性获取事件ID
      const eventId = eventEl.getAttribute('data-event-id')
      const calendarId = eventEl.getAttribute('data-calendar-id')
      if (eventId && calendarId) {
        const event = calendarInstance?.getEvent(eventId, calendarId)
        if (event) {
          showDetailDialog(event as unknown as CalendarEvent)
        }
      }
    }
  })

  // 也用TOAST UI自带的clickEvent作为备用
  calendarInstance.on('clickEvent', ({ event }: any) => {
    if (event) {
      showDetailDialog(event as unknown as CalendarEvent)
    }
  })

  calendarInstance.on('beforeCreateEvent', (eventData: any) => {
    // 在日历上拖拽选择时间段，打开新增排课对话框
    const startDate = eventData.start.toDate()
    const endDate = eventData.end.toDate()
    const startDateStr = startDate.toISOString().split('T')[0]

    form.value = {
      class_plan_id: undefined,
      teacher_id: undefined,
      classroom_id: undefined,
      schedule_date: startDateStr,
      start_time: formatTime(startDate),
      end_time: formatTime(endDate),
      lesson_hours: 2,
      title: '',
      notes: '',
    }
    editingItem.value = null
    dialogVisible.value = true
  })

  updateDateRange()  // 初始化日期范围显示
  loadCalendarEvents()
}

const getCalendarColor = (index: number) => {
  const colors = ['#3788d8', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4']
  return colors[index % colors.length]
}

const formatTime = (date: Date) => {
  return date.toTimeString().slice(0, 8)
}

const showDialog = (event?: CalendarEvent) => {
  editingItem.value = event || null
  if (event && event.raw) {
    const raw = event.raw
    const startDate = new Date(event.start)
    const endDate = new Date(event.end)
    form.value = {
      class_plan_id: raw.class_plan_id,
      teacher_id: raw.teacher_id,
      classroom_id: raw.classroom_id,
      schedule_date: startDate.toISOString().split('T')[0] as string,
      start_time: formatTime(startDate),
      end_time: formatTime(endDate),
      lesson_hours: raw.lesson_hours,
      title: event.title || '',
      status: raw.status,
      notes: raw.notes ?? '',
    }
  } else {
    const now = new Date()
    form.value = {
      class_plan_id: undefined,
      teacher_id: undefined,
      classroom_id: undefined,
      schedule_date: now.toISOString().split('T')[0] as string,
      start_time: '09:00:00',
      end_time: '11:00:00',
      lesson_hours: 2,
      title: '',
      notes: '',
    }
  }
  dialogVisible.value = true
}

// 显示课程详情弹窗
const showDetailDialog = async (event: CalendarEvent) => {
  detailEvent.value = event
  detailStudents.value = []
  scheduleAttendances.value = []
  detailDialogVisible.value = true

  // 加载学生出勤信息 - 注意：raw里的排课ID字段是schedule_id不是id
  if (event.raw?.schedule_id) {
    loadingStudents.value = true
    try {
      const res = await getScheduleAttendances(event.raw.schedule_id)
      scheduleAttendances.value = res || []
    } catch {
      // 忽略错误，回退到加载报名学生
      if (event.raw?.class_plan_id) {
        const enrollRes = await getEnrollments({
          class_plan_id: event.raw.class_plan_id,
          page_size: 100,
          status: 'active',
        })
        detailStudents.value = enrollRes.data?.items || []
      }
    } finally {
      loadingStudents.value = false
    }
  }
}

// 处理出勤状态变更
const handleAttendanceChange = async (item: ScheduleAttendanceItem) => {
  if (!detailEvent.value?.raw?.schedule_id) return

  try {
    await markAttendance({
      enrollment_id: item.enrollment_id,
      schedule_id: detailEvent.value.raw.schedule_id,
      status: item.status,
      leave_reason: item.leave_reason,
      deduct_hours: item.status === 'absent', // 缺勤默认扣课时
    })
    ElMessage.success('出勤状态已更新')
  } catch {
    ElMessage.error('更新出勤状态失败')
  }
}

// 从详情弹窗跳转到编辑
const editFromDetail = () => {
  if (detailEvent.value) {
    detailDialogVisible.value = false
    showDialog(detailEvent.value)
  }
}

// 格式化事件时间
const formatEventTime = (event: CalendarEvent) => {
  if (!event.start || !event.end) return '-'
  const startDate = new Date(event.start)
  const endDate = new Date(event.end)
  const dateStr = startDate.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
  const startTime = startDate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  const endTime = endDate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  return `${dateStr} ${startTime} - ${endTime}`
}

// 状态相关 - 从数据字典取
const getStatusType = (status?: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
  if (!status) return 'info'
  const color = scheduleStatusOptions.value.find(i => i.value === status)?.color
  // 确保返回有效的el-tag type
  if (color && ['primary', 'success', 'warning', 'danger', 'info'].includes(color)) {
    return color as 'primary' | 'success' | 'warning' | 'danger' | 'info'
  }
  return 'primary'
}

const getStatusLabel = (status?: string) => {
  if (!status) return '未知'
  return scheduleStatusOptions.value.find(i => i.value === status)?.label || status
}

const handleSave = async () => {
  await formRef.value?.validate()
  if (!form.value.class_plan_id) return // 确保班级已选择

  // 教室容量校验：如果选择了教室，检查容量是否足够
  if (form.value.classroom_id) {
    const classroom = allClassrooms.value.find(r => r.id === form.value.classroom_id)
    const classPlan = allClassPlans.value.find(c => c.id === form.value.class_plan_id)
    if (classroom && classPlan && classroom.capacity && classroom.capacity < classPlan.current_students) {
      try {
        await ElMessageBox.confirm(
          `该教室容量为 ${classroom.capacity} 人，但班级已报名 ${classPlan.current_students} 人。\n是否继续排课？`,
          '⚠️ 教室容量不足',
          {
            confirmButtonText: '继续排课',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
      } catch {
        saving.value = false
        return  // 用户取消
      }
    }
  }

  saving.value = true
  try {
    // 检测排课冲突
    const conflictRes = await checkScheduleConflicts({
      class_plan_id: form.value.class_plan_id!,
      teacher_id: form.value.teacher_id,
      classroom_id: form.value.classroom_id,
      schedule_date: form.value.schedule_date,
      start_time: form.value.start_time,
      end_time: form.value.end_time,
      exclude_schedule_id: editingItem.value?.raw?.schedule_id,
    })

    if (conflictRes?.has_conflict) {
      // 有冲突，弹出确认框
      const conflictMessages = conflictRes?.conflicts?.map(c => `• ${c.message}`).join('\n') || ''
      try {
        await ElMessageBox.confirm(
          `检测到以下冲突：\n\n${conflictMessages}\n\n是否仍然继续保存？`,
          '⚠️ 排课冲突警告',
          {
            confirmButtonText: '仍然保存',
            cancelButtonText: '取消',
            type: 'warning',
            dangerouslyUseHTMLString: false,
          }
        )
      } catch {
        // 用户点击取消
        saving.value = false
        return
      }
    }

    if (editingItem.value && editingItem.value.raw) {
      await updateSchedule(editingItem.value.raw.schedule_id, {
        teacher_id: form.value.teacher_id,
        classroom_id: form.value.classroom_id,
        schedule_date: form.value.schedule_date,
        start_time: form.value.start_time,
        end_time: form.value.end_time,
        lesson_hours: form.value.lesson_hours,
        title: form.value.title,
        status: form.value.status,
        notes: form.value.notes,
      })
      ElMessage.success('更新成功')
    } else {
      await createSchedule({ ...form.value, class_plan_id: form.value.class_plan_id })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadCalendarEvents()
  } finally {
    saving.value = false
  }
}

const handleDelete = async () => {
  if (!editingItem.value || !editingItem.value.raw) return

  await ElMessageBox.confirm('确定删除该排课记录？', '确认删除', {
    type: 'warning',
  })

  await deleteSchedule(editingItem.value.raw.schedule_id)
  ElMessage.success('删除成功')
  dialogVisible.value = false
  loadCalendarEvents()
}

// Batch schedule methods
const showBatchDialog = () => {
  const now = new Date()
  const nextMonth = new Date(now)
  nextMonth.setMonth(nextMonth.getMonth() + 1)

  const startDateStr = now.toISOString().split('T')[0] as string
  const endDateStr = nextMonth.toISOString().split('T')[0] as string

  batchForm.value = {
    class_plan_id: undefined,
    teacher_id: undefined,
    classroom_id: undefined,
    dateRanges: [{ range: [startDateStr, endDateStr] }],
    timeSlots: [{ weekdays: [], start_time: '09:00:00', end_time: '11:00:00' }],
    lesson_hours: 2,
    title: '',
    notes: '',
  }
  batchDialogVisible.value = true
}

// 构建批量创建请求数据（抽取公共逻辑）
const buildBatchCreateData = (): ScheduleBatchCreate | null => {
  if (!batchForm.value.class_plan_id) return null

  // 过滤出有效的日期范围
  const validDateRanges = batchForm.value.dateRanges
    .filter(r => r.range && r.range[0] && r.range[1])
    .map(r => ({
      start_date: r.range![0],
      end_date: r.range![1],
    }))
  if (validDateRanges.length === 0) {
    ElMessage.warning('请至少设置一个日期范围')
    return null
  }

  // 过滤出有效的时间段（有选中周几的）
  const validSlots = batchForm.value.timeSlots.filter(slot => slot.weekdays.length > 0)
  if (validSlots.length === 0) {
    ElMessage.warning('请至少选择一个上课日')
    return null
  }

  return {
    class_plan_id: batchForm.value.class_plan_id,
    teacher_id: batchForm.value.teacher_id,
    classroom_id: batchForm.value.classroom_id,
    date_ranges: validDateRanges,
    time_slots: validSlots.map(slot => ({
      weekdays: slot.weekdays,
      start_time: slot.start_time,
      end_time: slot.end_time,
    })),
    lesson_hours: batchForm.value.lesson_hours,
    title: batchForm.value.title || undefined,
    notes: batchForm.value.notes || undefined,
  }
}

// 格式化冲突信息用于显示（HTML格式）
const formatConflictHtml = (conflicts: BatchConflictItem[]): string => {
  // 按日期排序
  const sorted = [...conflicts].sort((a, b) => a.schedule_date.localeCompare(b.schedule_date))

  // 最多显示15条
  const displayItems = sorted.slice(0, 15)
  const rows = displayItems.map(c => {
    const dateStr = c.schedule_date
    const timeStr = `${c.start_time.slice(0, 5)}-${c.end_time.slice(0, 5)}`
    const typeIcon = c.conflict_type === 'teacher' ? '👨‍🏫' : '🏫'
    return `
      <tr>
        <td style="padding: 6px 8px; border-bottom: 1px solid #f0f0f0; white-space: nowrap;">${dateStr}</td>
        <td style="padding: 6px 8px; border-bottom: 1px solid #f0f0f0; white-space: nowrap;">${timeStr}</td>
        <td style="padding: 6px 8px; border-bottom: 1px solid #f0f0f0;">${typeIcon} ${c.conflict_with}</td>
      </tr>
    `
  })

  let html = `
    <div style="max-height: 350px; overflow-y: auto; margin: 12px 0;">
      <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
        <thead>
          <tr style="background: #f5f7fa;">
            <th style="padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e4e7ed;">日期</th>
            <th style="padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e4e7ed;">时间</th>
            <th style="padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e4e7ed;">冲突原因</th>
          </tr>
        </thead>
        <tbody>
          ${rows.join('')}
        </tbody>
      </table>
    </div>
  `

  if (sorted.length > 15) {
    html += `<div style="color: #909399; font-size: 12px; text-align: center; margin-top: 8px;">... 还有 ${sorted.length - 15} 条冲突未显示</div>`
  }

  return html
}

const handleBatchSave = async () => {
  await batchFormRef.value?.validate()

  const data = buildBatchCreateData()
  if (!data) return

  batchSaving.value = true
  try {
    // 第一步：预检测冲突
    const previewRes = await batchPreviewSchedule(data)
    const total_count = previewRes?.total_count || 0
    const conflict_count = previewRes?.conflict_count || 0
    const conflicts = previewRes?.conflicts || []

    // 如果全都冲突了，直接提示不创建
    if (conflict_count > 0 && conflict_count === total_count) {
      ElMessage.error(`全部 ${total_count} 条排课都有冲突，无法创建`)
      return
    }

    // 计算无冲突的排课数量
    let canCreateCount = total_count - conflict_count

    // 第二步：课时校验 - 检查每个学生是否超出购买课时
    let finalCreateData = data  // 可能会被修改（如果用户选择"排到购买课时"）
    try {
      const hoursSummary = await getClassPlanHoursSummary(data.class_plan_id)
      if (hoursSummary && hoursSummary.students && hoursSummary.students.length > 0) {
        const newHours = canCreateCount * data.lesson_hours
        const classScheduledHours = hoursSummary.class_scheduled_hours || 0

        // 找出会超额的学生
        const overStudents = hoursSummary.students.filter(s => s.available_hours < newHours)

        if (overStudents.length > 0) {
          // 计算按最小可排课时，最多能排多少节
          const minAvailable = hoursSummary.min_available_hours || 0
          const maxCanSchedule = Math.max(0, Math.floor(minAvailable / data.lesson_hours))

          // 构建学生详情表格HTML
          const studentsTableHtml = hoursSummary.students.map(s => {
            const willOver = s.available_hours < newHours
            const overAmount = newHours - s.available_hours
            const rowStyle = willOver ? 'background: #fef0f0;' : ''
            const nameStyle = willOver ? 'color: #f56c6c; font-weight: 600;' : ''
            const overCell = willOver
              ? `<td style="padding: 6px 8px; color: #f56c6c; font-weight: 600;">超${overAmount.toFixed(1)}</td>`
              : `<td style="padding: 6px 8px; color: #67c23a;">✓</td>`
            return `
              <tr style="${rowStyle}">
                <td style="padding: 6px 8px; ${nameStyle}">${s.student_name}</td>
                <td style="padding: 6px 8px; text-align: center;">${s.purchased_hours}</td>
                <td style="padding: 6px 8px; text-align: center;">${s.used_hours}</td>
                <td style="padding: 6px 8px; text-align: center;">${s.scheduled_hours}</td>
                <td style="padding: 6px 8px; text-align: center; ${willOver ? 'color: #f56c6c;' : ''}">${s.available_hours.toFixed(1)}</td>
                ${overCell}
              </tr>
            `
          }).join('')

          const hoursHtml = `
            <div style="margin-bottom: 12px; font-size: 14px;">
              <p style="margin: 0 0 8px 0;">
                本次排课 <strong style="color: #409eff;">${canCreateCount}</strong> 节 × ${data.lesson_hours} 课时 =
                <strong style="color: #409eff;">${newHours}</strong> 课时
              </p>
              <p style="margin: 0; color: #f56c6c;">
                ⚠️ ${overStudents.length}/${hoursSummary.total_students} 位学生课时将超额：
              </p>
            </div>
            <div style="max-height: 280px; overflow-y: auto; margin-bottom: 12px;">
              <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                <thead>
                  <tr style="background: #f5f7fa;">
                    <th style="padding: 8px; text-align: left; font-weight: 600; border-bottom: 2px solid #e4e7ed;">学生</th>
                    <th style="padding: 8px; text-align: center; font-weight: 600; border-bottom: 2px solid #e4e7ed;">购买</th>
                    <th style="padding: 8px; text-align: center; font-weight: 600; border-bottom: 2px solid #e4e7ed;">已用</th>
                    <th style="padding: 8px; text-align: center; font-weight: 600; border-bottom: 2px solid #e4e7ed;">已排</th>
                    <th style="padding: 8px; text-align: center; font-weight: 600; border-bottom: 2px solid #e4e7ed;">可排</th>
                    <th style="padding: 8px; text-align: center; font-weight: 600; border-bottom: 2px solid #e4e7ed;">状态</th>
                  </tr>
                </thead>
                <tbody>
                  ${studentsTableHtml}
                </tbody>
              </table>
            </div>
          `

          // 根据是否有剩余可排课时，显示不同的选项
          if (maxCanSchedule > 0) {
            // 有剩余可排课时，显示三选项
            const userChoice = await new Promise<'continue' | 'limit' | 'cancel'>((resolve) => {
              ElMessageBox({
                title: '⏰ 课时超额提醒',
                message: `
                  ${hoursHtml}
                  <div style="padding: 10px 12px; background: #e6f7ff; border: 1px solid #91d5ff; border-radius: 4px; font-size: 12px; color: #1890ff; margin-bottom: 12px;">
                    💡 按最小可排课时（${minAvailable.toFixed(1)}）计算，最多可排 <strong>${maxCanSchedule}</strong> 节课
                  </div>
                  <div style="display: flex; flex-direction: column; gap: 8px;">
                    <div style="padding: 10px 12px; background: #f0f9eb; border: 1px solid #e1f3d8; border-radius: 4px; cursor: pointer;"
                         onclick="window.__hoursLimitChoice='continue'; document.querySelector('.el-message-box__close').click()">
                      <strong style="color: #67c23a;">① 继续排课</strong>
                      <span style="color: #909399; font-size: 12px; margin-left: 8px;">忽略超限，排全部 ${canCreateCount} 节</span>
                    </div>
                    <div style="padding: 10px 12px; background: #fdf6ec; border: 1px solid #faecd8; border-radius: 4px; cursor: pointer;"
                         onclick="window.__hoursLimitChoice='limit'; document.querySelector('.el-message-box__close').click()">
                      <strong style="color: #e6a23c;">② 排到购买课时</strong>
                      <span style="color: #909399; font-size: 12px; margin-left: 8px;">按时间顺序，只排 ${maxCanSchedule} 节（所有学生不超额）</span>
                    </div>
                    <div style="padding: 10px 12px; background: #fef0f0; border: 1px solid #fde2e2; border-radius: 4px; cursor: pointer;"
                         onclick="window.__hoursLimitChoice='cancel'; document.querySelector('.el-message-box__close').click()">
                      <strong style="color: #f56c6c;">③ 取消</strong>
                      <span style="color: #909399; font-size: 12px; margin-left: 8px;">放弃本次排课</span>
                    </div>
                  </div>
                `,
                dangerouslyUseHTMLString: true,
                showConfirmButton: false,
                showCancelButton: false,
                showClose: true,
                customStyle: { width: '580px' },
                closeOnClickModal: false,
              }).catch(() => {
                // 用户关闭对话框
              }).finally(() => {
                const choice = (window as any).__hoursLimitChoice || 'cancel'
                delete (window as any).__hoursLimitChoice
                resolve(choice)
              })
            })

            if (userChoice === 'cancel') {
              return
            } else if (userChoice === 'limit') {
              // 限制排课数量 - 传递max_count参数给后端
              finalCreateData = { ...data, max_count: maxCanSchedule }
              canCreateCount = maxCanSchedule
              ElMessage.info(`将按时间顺序只排 ${maxCanSchedule} 节课，所有学生都不超额`)
            }
            // continue: 继续排课，不做修改
          } else {
            // 没有剩余可排课时（所有学生都已排满），只显示两选项
            try {
              await ElMessageBox.confirm(
                `${hoursHtml}
                <div style="padding: 12px; background: #fef0f0; border-radius: 4px; font-size: 13px; color: #f56c6c;">
                  ⚠️ 所有学生剩余课时不足，继续排课将全部超额！
                </div>`,
                '⏰ 课时超额提醒',
                {
                  confirmButtonText: `继续排课（忽略超限）`,
                  cancelButtonText: '取消',
                  type: 'warning',
                  dangerouslyUseHTMLString: true,
                  customStyle: { width: '580px' },
                }
              )
            } catch {
              return
            }
          }
        }
      }
    } catch (e) {
      // 获取课时统计失败，继续排课（不阻塞）
      console.warn('获取课时统计失败，跳过校验', e)
    }

    // 如果有部分冲突，弹窗让用户确认
    if (conflict_count > 0) {
      const conflictHtml = formatConflictHtml(conflicts)

      const summaryHtml = `
        <div style="margin-bottom: 12px; font-size: 14px; line-height: 1.6;">
          <p style="margin: 0 0 8px 0;">
            计划创建 <strong style="color: #409eff;">${total_count}</strong> 条排课，
            其中 <strong style="color: #f56c6c;">${conflict_count}</strong> 条存在冲突：
          </p>
        </div>
        ${conflictHtml}
        <div style="margin-top: 16px; padding: 12px; background: #fdf6ec; border-radius: 4px; font-size: 13px; color: #e6a23c;">
          💡 点击「跳过冲突继续」将创建 <strong>${canCreateCount}</strong> 条无冲突的排课
        </div>
      `

      try {
        await ElMessageBox.confirm(
          summaryHtml,
          '⚠️ 检测到排课冲突',
          {
            confirmButtonText: `跳过冲突，创建 ${canCreateCount} 条`,
            cancelButtonText: '取消',
            type: 'warning',
            distinguishCancelAndClose: true,
            dangerouslyUseHTMLString: true,
            customStyle: { width: '550px' },
          }
        )
      } catch {
        // 用户点击取消
        return
      }
    }

    // 第三步：实际创建（跳过冲突，可能有max_count限制）
    const res = await batchCreateSchedule(finalCreateData)
    if (res?.batch_no) {
      lastBatchNo.value = res.batch_no
    }

    // 显示创建结果
    if (res?.skipped_count && res?.skipped_count > 0) {
      ElMessage.success(`成功创建 ${res.created_count} 条排课，已跳过 ${res.skipped_count} 条冲突`)
    } else if (res?.created_count) {
      ElMessage.success(`成功创建 ${res.created_count} 条排课记录`)
    }
    batchDialogVisible.value = false
    loadCalendarEvents()
  } finally {
    batchSaving.value = false
  }
}

// Batch operation methods - 从详情弹窗进入的批量操作
const showBatchOperationDialog = async () => {
  if (!detailEvent.value?.raw?.batch_no) return

  const batchNo = detailEvent.value.raw.batch_no
  batchOperationBatchNo.value = batchNo
  batchOperationTab.value = 'update'
  batchSchedules.value = []
  selectedScheduleIds.value = []
  batchUpdateForm.value = {
    teacher_id: undefined,
    classroom_id: undefined,
    notes: '',
  }

  // 关闭详情弹窗，打开批量操作弹窗
  detailDialogVisible.value = false
  batchOperationDialogVisible.value = true

  // 加载批次的所有排课
  loadingBatchSchedules.value = true
  try {
    const res = await getBatchSchedules(batchNo)
    batchSchedules.value = res || []

    // 默认选中所有可操作的排课（排除已完成的）
    await nextTick()
    if (batchTableRef.value) {
      batchSchedules.value.forEach(row => {
        // 只选中非已完成状态的排课
        if (row.status !== 'completed') {
          batchTableRef.value.toggleRowSelection(row, true)
        }
      })
    }
  } catch {
    ElMessage.error('加载批次排课失败')
  } finally {
    loadingBatchSchedules.value = false
  }
}

// 批量更新
const handleBatchUpdate = async () => {
  if (selectedScheduleIds.value.length === 0) {
    ElMessage.warning('请至少选择一条排课')
    return
  }

  // 检查是否有要更新的内容
  const form = batchUpdateForm.value
  if (!form.teacher_id && !form.classroom_id && !form.notes) {
    ElMessage.warning('请至少选择一项要更新的内容')
    return
  }

  batchUpdating.value = true
  try {
    const updateData: ScheduleBatchUpdate = {
      schedule_ids: selectedScheduleIds.value,
    }
    if (form.teacher_id) updateData.teacher_id = form.teacher_id
    if (form.classroom_id) updateData.classroom_id = form.classroom_id
    if (form.notes) updateData.notes = form.notes

    const res = await batchUpdateSchedules(updateData)
    ElMessage.success(res?.message || '操作成功')
    batchOperationDialogVisible.value = false
    loadCalendarEvents()
  } catch {
    ElMessage.error('批量更新失败')
  } finally {
    batchUpdating.value = false
  }
}

// 从批量操作弹窗中删除
const handleBatchDeleteFromDialog = async () => {
  if (selectedScheduleIds.value.length === 0) {
    ElMessage.warning('请至少选择一条排课')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedScheduleIds.value.length} 条排课记录吗？此操作不可恢复！`,
      '⚠️ 确认批量删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch {
    return  // 用户取消
  }

  batchDeleting.value = true
  try {
    const res = await batchDeleteSchedules({ schedule_ids: selectedScheduleIds.value })
    ElMessage.success(res?.message || '操作成功')
    batchOperationDialogVisible.value = false
    loadCalendarEvents()
  } finally {
    batchDeleting.value = false
  }
}

// Watch filters - 添加守卫防止组件卸载后触发
watch([filterClassPlan, filterTeacher], () => {
  if (isMounted && calendarInstance) {
    loadCalendarEvents()
  }
})

// 选择班级后自动带出教师和教室（仅在新增排课时）
watch(() => form.value.class_plan_id, (newClassPlanId) => {
  if (!editingItem.value && newClassPlanId) {
    const classPlan = allClassPlans.value.find(c => c.id === newClassPlanId)
    if (classPlan) {
      // 自动带出教师（如果班级有设置）
      if (classPlan.teacher_id) {
        form.value.teacher_id = classPlan.teacher_id
      }
      // 自动带出教室（如果班级有设置）
      if (classPlan.classroom_id) {
        form.value.classroom_id = classPlan.classroom_id
      }
    }
  }
})

// 批量排课也要自动带出
watch(() => batchForm.value.class_plan_id, (newClassPlanId) => {
  if (newClassPlanId) {
    const classPlan = allClassPlans.value.find(c => c.id === newClassPlanId)
    if (classPlan) {
      if (classPlan.teacher_id) {
        batchForm.value.teacher_id = classPlan.teacher_id
      }
      if (classPlan.classroom_id) {
        batchForm.value.classroom_id = classPlan.classroom_id
      }
    }
  }
})

// Track if component is mounted
let isMounted = false

// 清理日历实例的函数
const cleanupCalendar = () => {
  if (calendarInstance) {
    try {
      // 先移除事件监听
      calendarInstance.off('clickEvent')
      calendarInstance.off('beforeCreateEvent')
      // 清空日历内容
      calendarInstance.clear()
    } catch {
      // 忽略错误
    }

    // 手动清空 DOM 内容，防止 destroy 时操作已被 Vue 清理的 DOM
    if (calendarRef.value) {
      calendarRef.value.innerHTML = ''
    }

    // 不调用 destroy - 这个SB方法会导致 parentNode null 错误
    // calendarInstance.destroy()
    calendarInstance = null
  }
}

// 路由离开前清理 - 在 Vue 开始卸载 DOM 之前执行
onBeforeRouteLeave((_to, _from, next) => {
  isMounted = false
  cleanupCalendar()
  next()
})

onMounted(async () => {
  isMounted = true
  await loadOptions()
  await nextTick()
  if (isMounted) {
    initCalendar()
  }
})

onBeforeUnmount(() => {
  // 双重保险：如果路由守卫没触发，这里也清理
  isMounted = false
  cleanupCalendar()
})
</script>

<style scoped lang="scss">
.schedule-view {
  padding: 20px;
  height: calc(100vh - 60px); // 减去顶部导航栏高度
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
  }

  .date-nav {
    display: flex;
    align-items: center;
    gap: 12px;

    .current-date {
      font-size: 15px;
      font-weight: 500;
      color: var(--text-primary);
      min-width: 180px;
    }
  }

  .header-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }
}

.calendar-container {
  flex: 1;
  min-height: 0; // 让flex子项可以收缩
  background: white;
  border-radius: 8px;
  overflow: hidden; // 隐藏溢出，让内部滚动

  .calendar {
    height: 100%;
  }
}

// TOAST UI Calendar overrides - 让日历自适应容器高度
:deep(.toastui-calendar-layout) {
  height: 100% !important;
}

:deep(.toastui-calendar-week-view) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
}

:deep(.toastui-calendar-panel.toastui-calendar-time) {
  flex: 1 !important;
  height: auto !important;
  min-height: 0 !important;
  overflow-y: auto !important;
}

// 时间网格 - 使用合适的固定高度让内容可滚动
:deep(.toastui-calendar-timegrid) {
  height: 900px !important;
}

:deep(.toastui-calendar-timegrid-scroll-area) {
  height: 900px !important;
}

:deep(.toastui-calendar-timegrid-time-column) {
  height: 900px !important;
}

:deep(.toastui-calendar-timegrid-hour-rows) {
  height: 900px !important;
}

:deep(.toastui-calendar-timegrid-time) {
  height: 60px !important;
}

:deep(.toastui-calendar-time) {
  font-size: 12px;
}

// 月视图事件状态样式
.month-event {
  &.status-completed {
    opacity: 0.7;
  }

  &.status-cancelled {
    opacity: 0.5;
    text-decoration: line-through;
  }
}

// 月视图日期样式
:deep(.toastui-calendar-grid-cell-header) {
  .today {
    color: #fff;
    background: #409eff;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
  }

  .other-month {
    color: #c0c4cc;
  }
}

:deep(.toastui-calendar-event-time) {
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.4;
  overflow: hidden;

  // 课表卡片样式
  .schedule-card {
    display: flex;
    flex-direction: column;
    gap: 4px;
    height: 100%;
  }

  .schedule-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    margin-bottom: 2px;
  }

  .schedule-time {
    font-size: 11px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.85);
    background: rgba(0, 0, 0, 0.15);
    padding: 1px 4px;
    border-radius: 3px;
  }

  .schedule-status {
    font-size: 10px;
    font-weight: 500;
    padding: 1px 5px;
    border-radius: 3px;
    white-space: nowrap;

    &.status-scheduled {
      background: rgba(255, 255, 255, 0.25);
      color: #fff;
    }

    &.status-completed {
      background: rgba(103, 194, 58, 0.9);
      color: #fff;
    }

    &.status-cancelled {
      background: rgba(245, 108, 108, 0.9);
      color: #fff;
    }
  }

  .schedule-title {
    font-weight: 600;
    font-size: 14px;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .schedule-class {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.8);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: -2px;
  }

  .schedule-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.9);
  }

  .info-row {
    display: flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;

    // 请假人数 - 橙色
    .leave-text {
      color: #ffc107;
      font-weight: 500;
    }

    // 缺勤人数 - 红色
    .absent-text {
      color: #ff6b6b;
      font-weight: 500;
    }
  }

  // 自定义图标样式（用CSS绘制简单图标）
  .info-icon {
    display: inline-block;
    width: 12px;
    height: 12px;
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
    opacity: 0.9;

    &.teacher {
      // 小人图标
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'/%3E%3C/svg%3E");
    }

    &.room {
      // 位置/房间图标
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z'/%3E%3C/svg%3E");
    }

    &.student {
      // 多人/学生图标
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z'/%3E%3C/svg%3E");
    }
  }
}

// 课程详情弹窗样式
.schedule-detail {
  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
    }
  }

  .student-list-section {
    margin-top: 20px;

    .section-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
      font-weight: 600;
      color: #303133;
    }

    .student-list {
      max-height: 240px;
      overflow-y: auto;
      border: 1px solid #ebeef5;
      border-radius: 4px;
      padding: 8px;

      .student-item {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        border-bottom: 1px solid #f0f0f0;

        &:last-child {
          border-bottom: none;
        }

        .student-name {
          flex: 1;
          font-weight: 500;
        }

        .student-phone {
          color: #909399;
          font-size: 13px;
          margin-right: 12px;
        }
      }
    }
  }
}

// 日期范围配置样式
.date-ranges-form-item {
  :deep(.el-form-item__content) {
    display: block;
  }
}

.date-ranges-container {
  width: 100%;

  .date-ranges-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #ebeef5;

    .header-title {
      font-size: 14px;
      color: #606266;
    }
  }

  .date-ranges-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .date-range-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .date-ranges-hint {
    margin-top: 10px;
    font-size: 12px;
    color: #909399;
  }
}

// 时间段配置样式
.time-slots-form-item {
  :deep(.el-form-item__content) {
    display: block;
  }
}

.time-slots-container {
  width: 100%;

  .time-slots-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #ebeef5;

    .header-title {
      font-size: 14px;
      color: #606266;
    }
  }

  .time-slots-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .time-slot-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    background: #f9fafc;
    border-radius: 6px;
    border: 1px solid #ebeef5;

    .weekday-select {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .time-separator {
      color: #909399;
      font-weight: 500;
    }
  }

  .time-slots-hint {
    margin-top: 10px;
    font-size: 12px;
    color: #909399;
  }
}

// 批次号信息样式
.batch-info {
  display: flex;
  align-items: center;
  gap: 12px;

  code {
    background: #f5f7fa;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 12px;
    color: #606266;
  }
}

// 批量操作弹窗样式
.batch-operation-content {
  .batch-header {
    margin-bottom: 16px;
  }

  .batch-schedule-list {
    margin-bottom: 16px;

    .list-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
      font-weight: 600;
      color: #303133;
    }

    .batch-tip {
      margin-top: 8px;
      padding: 4px 8px;
      background: #fdf6ec;
      border-radius: 4px;
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }

  .batch-actions {
    border-top: 1px solid #ebeef5;
    padding-top: 8px;
  }
}

.batch-dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;

  .selection-info {
    color: #606266;
    font-size: 14px;

    strong {
      color: #409eff;
    }
  }

  .footer-buttons {
    display: flex;
    gap: 8px;
  }
}
</style>
