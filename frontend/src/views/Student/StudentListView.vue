<template>
  <div class="student-view">
    <div class="page-header">
      <h1>学生管理</h1>
      <el-button v-permission="['student', 'edit']" type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon>
        新增学生
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
      <el-select v-model="filterStatus" placeholder="学生状态" clearable style="width: 120px">
        <el-option
          v-for="item in statusOptions"
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
      <el-select v-model="filterSource" placeholder="来源" clearable style="width: 120px">
        <el-option
          v-for="item in sourceOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-button @click="handleSearch">搜索</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- Table -->
    <el-table :data="students" v-loading="loading" stripe>
      <el-table-column prop="name" label="姓名" min-width="80">
        <template #default="{ row }">
          <el-button link type="primary" @click="showStudentDetail(row)">{{ row.name }}</el-button>
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="电话" min-width="120" />
      <el-table-column prop="gender" label="性别" width="60" align="center">
        <template #default="{ row }">
          {{ getGenderLabel(row.gender) }}
        </template>
      </el-table-column>
      <el-table-column prop="grade" label="年级" min-width="80">
        <template #default="{ row }">
          {{ getGradeLabel(row.grade) || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="school" label="学校" min-width="100" show-overflow-tooltip />
      <el-table-column prop="parent_name" label="家长" min-width="80" show-overflow-tooltip />
      <el-table-column prop="parent_phone" label="家长电话" min-width="120" />
      <el-table-column prop="total_hours" label="课时" width="80" align="center">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="showHoursDetail(row)" class="hours-link">
            <el-tag size="small" :type="row.remaining_hours > 5 ? 'success' : row.remaining_hours > 0 ? 'warning' : 'danger'">
              {{ row.total_hours }}
            </el-tag>
          </el-button>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
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
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="showAttendanceDialog(row)">出勤</el-button>
          <el-button v-permission="['student', 'edit']" link type="primary" size="small" @click="showDialog(row)">编辑</el-button>
          <el-popconfirm v-permission="['student', 'delete']" title="确定删除该学生？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button link type="danger" size="small">删除</el-button>
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
      :title="editingItem ? '编辑学生' : '新增学生'"
      width="700px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="form.name" placeholder="请输入学生姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话" prop="phone">
              <el-input v-model="form.phone" placeholder="必填，用于创建登录账号" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
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
          <el-col :span="8">
            <el-form-item label="出生日期" prop="birthday">
              <el-date-picker
                v-model="form.birthday"
                type="date"
                placeholder="选择日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="年级" prop="grade">
              <el-select v-model="form.grade" placeholder="请选择" style="width: 100%">
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
            <el-form-item label="学校" prop="school">
              <el-input v-model="form.school" placeholder="请输入就读学校" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="来源" prop="source">
              <el-select v-model="form.source" placeholder="请选择" style="width: 100%">
                <el-option
                  v-for="item in sourceOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">家长信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="家长姓名" prop="parent_name">
              <el-input v-model="form.parent_name" placeholder="请输入家长姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="家长电话" prop="parent_phone">
              <el-input v-model="form.parent_phone" placeholder="请输入家长电话" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="家庭地址" prop="address">
          <el-input v-model="form.address" placeholder="请输入家庭地址" />
        </el-form-item>
        <el-divider content-position="left">学习标签</el-divider>
        <el-form-item label="科目水平" prop="subject_levels">
          <div class="subject-level-tags">
            <div v-for="subj in subjectOptions" :key="subj.value" class="subject-level-item">
              <span class="subject-name" :style="{ color: subj.color }">{{ subj.label }}</span>
              <el-select
                :model-value="getSubjectLevel(subj.value)"
                placeholder="--"
                clearable
                size="small"
                style="width: 90px"
                @change="(val: string) => setSubjectLevel(subj.value, val)"
              >
                <el-option
                  v-for="level in studentLevelOptions"
                  :key="level.value"
                  :label="level.label"
                  :value="level.value"
                />
              </el-select>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="学习目标" prop="learning_goals">
          <div class="subject-level-tags">
            <div v-for="subj in subjectOptions" :key="subj.value" class="subject-level-item">
              <span class="subject-name" :style="{ color: subj.color }">{{ subj.label }}</span>
              <el-select
                :model-value="getSubjectGoal(subj.value)"
                placeholder="--"
                clearable
                size="small"
                style="width: 100px"
                @change="(val: string) => setSubjectGoal(subj.value, val)"
              >
                <el-option
                  v-for="goal in learningGoalOptions"
                  :key="goal.value"
                  :label="goal.label"
                  :value="goal.value"
                />
              </el-select>
            </div>
          </div>
        </el-form-item>
        <el-divider content-position="left">其他信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学生状态" prop="status">
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
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 课时详情弹窗 -->
    <el-dialog
      v-model="hoursDialogVisible"
      :title="`${hoursStudent?.name || '学生'} - 课时详情`"
      width="600px"
    >
      <div v-loading="loadingHours">
        <div v-if="studentEnrollments.length > 0" class="hours-detail">
          <div class="hours-summary">
            <div class="summary-item">
              <span class="label">总购买课时</span>
              <span class="value">{{ hoursStudent?.total_hours || 0 }}</span>
            </div>
            <div class="summary-item">
              <span class="label">剩余课时</span>
              <span class="value" :class="{ danger: (hoursStudent?.remaining_hours || 0) <= 5 }">{{ hoursStudent?.remaining_hours || 0 }}</span>
            </div>
            <div class="summary-item">
              <span class="label">累计付款</span>
              <span class="value price">¥{{ Number(hoursStudent?.total_paid || 0).toFixed(0) }}</span>
            </div>
          </div>
          <el-divider content-position="left">各班级课时明细</el-divider>
          <el-table :data="studentEnrollments" stripe size="small">
            <el-table-column prop="class_plan.name" label="班级" min-width="150">
              <template #default="{ row }">
                {{ row.class_plan?.name || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="购买课时" width="90" align="center">
              <template #default="{ row }">
                {{ row.purchased_hours }}
              </template>
            </el-table-column>
            <el-table-column label="已用课时" width="90" align="center">
              <template #default="{ row }">
                {{ row.used_hours }}
              </template>
            </el-table-column>
            <el-table-column label="剩余课时" width="90" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="(row.purchased_hours - row.used_hours) > 5 ? 'success' : (row.purchased_hours - row.used_hours) > 0 ? 'warning' : 'danger'">
                  {{ row.purchased_hours - row.used_hours }}
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
                <el-tag size="small" :type="  getEnrollStatusType(row.status)">
                  {{ getEnrollStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <el-empty v-else description="暂无报名记录" />
      </div>
      <template #footer>
        <el-button @click="hoursDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 出勤记录弹窗 -->
    <el-dialog
      v-model="attendanceDialogVisible"
      :title="`${attendanceStudent?.name} - 出勤记录/请假`"
      width="800px"
    >
      <div class="attendance-content">
        <!-- Tab切换 -->
        <el-tabs v-model="attendanceTab">
          <el-tab-pane label="申请请假" name="leave">
            <div class="upcoming-schedules">
              <div v-if="loadingUpcoming" class="loading-tip">加载中...</div>
              <el-empty v-else-if="upcomingSchedules.length === 0" description="暂无未来课程安排" />
              <el-table v-else :data="upcomingSchedules" stripe size="small">
                <el-table-column prop="schedule_date" label="上课日期" width="110" />
                <el-table-column label="时间" width="140">
                  <template #default="{ row }">
                    {{ row.start_time?.slice(0, 5) }} - {{ row.end_time?.slice(0, 5) }}
                  </template>
                </el-table-column>
                <el-table-column prop="class_plan_name" label="班级" min-width="120" />
                <el-table-column prop="title" label="课程内容" min-width="100" />
                <el-table-column label="状态" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag v-if="row.attendance_status === 'leave'" type="warning" size="small">已请假</el-tag>
                    <el-tag v-else-if="row.attendance_status === 'absent'" type="danger" size="small">缺勤</el-tag>
                    <el-tag v-else type="success" size="small">正常</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100" align="center">
                  <template #default="{ row }">
                    <el-button
                      v-if="row.attendance_status !== 'leave'"
                      link
                      type="warning"
                      size="small"
                      @click="showLeaveForm(row)"
                    >请假</el-button>
                    <span v-else class="leave-reason-hint" :title="row.leave_reason">
                      {{ row.leave_reason?.slice(0, 6) }}{{ row.leave_reason?.length > 6 ? '...' : '' }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>
          <el-tab-pane label="出勤历史" name="history">
            <div v-if="loadingAttendances" class="loading-tip">加载中...</div>
            <el-empty v-else-if="attendanceRecords.length === 0" description="暂无出勤记录" />
            <el-table v-else :data="attendanceRecords" stripe size="small">
              <el-table-column prop="schedule_date" label="日期" width="110" />
              <el-table-column prop="class_plan_name" label="班级" min-width="120" />
              <el-table-column label="出勤状态" width="100" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.status === 'normal'" type="success" size="small">正常</el-tag>
                  <el-tag v-else-if="row.status === 'leave'" type="warning" size="small">请假</el-tag>
                  <el-tag v-else-if="row.status === 'absent'" type="danger" size="small">缺勤</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="leave_reason" label="请假原因" min-width="150" />
              <el-table-column label="扣课时" width="80" align="center">
                <template #default="{ row }">
                  {{ row.deduct_hours ? '是' : '否' }}
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
      <template #footer>
        <el-button @click="attendanceDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 请假表单弹窗 -->
    <el-dialog v-model="leaveFormVisible" title="申请请假" width="400px">
      <el-form :model="leaveForm" label-width="80px">
        <el-form-item label="上课日期">
          <span>{{ leaveForm.schedule_date }} {{ leaveForm.start_time?.slice(0, 5) }} - {{ leaveForm.end_time?.slice(0, 5) }}</span>
        </el-form-item>
        <el-form-item label="班级">
          <span>{{ leaveForm.class_plan_name }}</span>
        </el-form-item>
        <el-form-item label="请假原因" required>
          <el-input
            v-model="leaveForm.leave_reason"
            type="textarea"
            :rows="3"
            placeholder="请输入请假原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="leaveFormVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingLeave" @click="submitLeave">确认请假</el-button>
      </template>
    </el-dialog>

    <!-- 学生详情弹窗 - 显示科目水平和学习目标 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`${detailStudent?.name || '学生'} - 学习信息`"
      width="550px"
    >
      <div v-if="detailStudent" class="student-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="姓名">{{ detailStudent.name }}</el-descriptions-item>
          <el-descriptions-item label="年级">{{ getGradeLabel(detailStudent.grade) || '-' }}</el-descriptions-item>
          <el-descriptions-item label="学校" :span="2">{{ detailStudent.school || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="detail-section">
          <h4>科目水平</h4>
          <div v-if="detailStudent.subject_levels?.length" class="tag-list">
            <div v-for="sl in detailStudent.subject_levels" :key="sl" class="level-tag">
              <span class="subject" :style="{ color: getSubjectColor(sl.split(':')[0] || '') }">
                {{ getSubjectLabel(sl.split(':')[0] || '') }}
              </span>
              <el-tag size="small" :type="getLevelTagType(sl.split(':')[1] || '')">
                {{ getStudentLevelLabel(sl.split(':')[1] || '') }}
              </el-tag>
            </div>
          </div>
          <el-empty v-else description="暂未设置" :image-size="60" />
        </div>

        <div class="detail-section">
          <h4>学习目标</h4>
          <div v-if="detailStudent.learning_goals?.length" class="tag-list">
            <div v-for="goal in detailStudent.learning_goals" :key="goal" class="level-tag">
              <span class="subject" :style="{ color: getSubjectColor(goal.split(':')[0] || '') }">
                {{ getSubjectLabel(goal.split(':')[0] || '') }}
              </span>
              <el-tag size="small" type="success">
                {{ getLearningGoalLabel(goal.split(':')[1] || '') }}
              </el-tag>
            </div>
          </div>
          <el-empty v-else description="暂未设置" :image-size="60" />
        </div>

        <div v-if="detailStudent.remark" class="detail-section">
          <h4>备注</h4>
          <div class="remark-text">{{ detailStudent.remark }}</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="showDialog(detailStudent!)">编辑</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  getStudents, createStudent, updateStudent, deleteStudent,
  type Student, type StudentCreate
} from '@/api/student'
import { getDictItems, type DictItem } from '@/api/dictionary'
import { getEnrollments, type Enrollment } from '@/api/enrollment'
import {
  getUpcomingSchedules, getStudentAttendances, applyLeaveForStudent,
  type UpcomingScheduleItem, type StudentAttendanceDetail
} from '@/api/attendance'

// State
const students = ref<Student[]>([])
const loading = ref(false)
const saving = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const filterStatus = ref('')
const filterGrade = ref('')
const filterSource = ref('')

// Dictionary options
const genderOptions = ref<DictItem[]>([])
const statusOptions = ref<DictItem[]>([])
const gradeOptions = ref<DictItem[]>([])
const sourceOptions = ref<DictItem[]>([])
const subjectOptions = ref<DictItem[]>([])
const studentLevelOptions = ref<DictItem[]>([])
const learningGoalOptions = ref<DictItem[]>([])

// Dialog
const dialogVisible = ref(false)
const editingItem = ref<Student | null>(null)
const formRef = ref<FormInstance>()
const form = ref<StudentCreate>({
  name: '',
  phone: '',
  gender: '',
  birthday: '',
  grade: '',
  school: '',
  parent_name: '',
  parent_phone: '',
  address: '',
  source: '',
  subject_levels: [],
  learning_goals: [],
  status: 'active',
  remark: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入学生姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入联系电话（用于创建登录账号）', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
}

// 课时详情弹窗
const hoursDialogVisible = ref(false)
const hoursStudent = ref<Student | null>(null)
const studentEnrollments = ref<Enrollment[]>([])
const loadingHours = ref(false)

// 出勤记录弹窗
const attendanceDialogVisible = ref(false)
const attendanceStudent = ref<Student | null>(null)
const attendanceTab = ref('leave')
const upcomingSchedules = ref<UpcomingScheduleItem[]>([])
const attendanceRecords = ref<StudentAttendanceDetail[]>([])
const loadingUpcoming = ref(false)
const loadingAttendances = ref(false)

// 请假表单
const leaveFormVisible = ref(false)
const submittingLeave = ref(false)
const leaveForm = ref<{
  schedule_id: number
  schedule_date: string
  start_time: string
  end_time: string
  class_plan_name: string
  leave_reason: string
}>({
  schedule_id: 0,
  schedule_date: '',
  start_time: '',
  end_time: '',
  class_plan_name: '',
  leave_reason: '',
})

// 学生详情弹窗
const detailDialogVisible = ref(false)
const detailStudent = ref<Student | null>(null)

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

const getGradeLabel = (value?: string) => {
  if (!value) return ''
  return gradeOptions.value.find(i => i.value === value)?.label || value
}

// 科目水平标签相关方法
const getSubjectLevel = (subject: string): string => {
  const levels = form.value.subject_levels || []
  const found = levels.find(sl => sl.startsWith(`${subject}:`))
  return found ? (found.split(':')[1] || '') : ''
}

const setSubjectLevel = (subject: string, level: string) => {
  const levels = form.value.subject_levels || []
  // 移除旧的该科目记录
  const filtered = levels.filter(sl => !sl.startsWith(`${subject}:`))
  // 如果有新level则添加
  if (level) {
    filtered.push(`${subject}:${level}`)
  }
  form.value.subject_levels = filtered
}

// 学习目标相关方法（格式: subject:goal）
const getSubjectGoal = (subject: string): string => {
  const goals = form.value.learning_goals || []
  const found = goals.find(g => g.startsWith(`${subject}:`))
  return found ? (found.split(':')[1] || '') : ''
}

const setSubjectGoal = (subject: string, goal: string) => {
  const goals = form.value.learning_goals || []
  // 移除旧的该科目记录
  const filtered = goals.filter(g => !g.startsWith(`${subject}:`))
  // 如果有新goal则添加
  if (goal) {
    filtered.push(`${subject}:${goal}`)
  }
  form.value.learning_goals = filtered
}

const getSubjectLabel = (value: string) => {
  return subjectOptions.value.find(i => i.value === value)?.label || value
}

const getSubjectColor = (value: string) => {
  return subjectOptions.value.find(i => i.value === value)?.color || '#6B7280'
}

const getStudentLevelLabel = (value: string) => {
  return studentLevelOptions.value.find(i => i.value === value)?.label || value
}

const getLearningGoalLabel = (value: string) => {
  return learningGoalOptions.value.find(i => i.value === value)?.label || value
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 根据学生水平返回tag类型
const getLevelTagType = (level: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
  const typeMap: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    'excellent': 'success',
    'good': '',
    'average': 'warning',
    'weak': 'danger',
  }
  return typeMap[level] || 'info'
}

// 显示学生详情弹窗
const showStudentDetail = (student: Student) => {
  detailStudent.value = student
  detailDialogVisible.value = true
}

// 报名状态相关
const getEnrollStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'active': 'success',
    'completed': 'info',
    'cancelled': 'danger',
  }
  return typeMap[status] || 'info'
}

const getEnrollStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    'active': '在读',
    'completed': '结业',
    'cancelled': '取消',
  }
  return labelMap[status] || status
}

// 显示课时详情
const showHoursDetail = async (student: Student) => {
  hoursStudent.value = student
  studentEnrollments.value = []
  hoursDialogVisible.value = true
  loadingHours.value = true

  try {
    const res = await getEnrollments({
      student_id: student.id,
      page_size: 100, // 获取所有报名记录
    })
    studentEnrollments.value = res.data?.items || []
  } catch {
    ElMessage.error('获取课时详情失败')
  } finally {
    loadingHours.value = false
  }
}

// 显示出勤记录弹窗
const showAttendanceDialog = async (student: Student) => {
  attendanceStudent.value = student
  attendanceDialogVisible.value = true
  attendanceTab.value = 'leave'
  upcomingSchedules.value = []
  attendanceRecords.value = []

  // 加载未来排课
  loadUpcomingSchedules(student.id)
  // 加载出勤历史
  loadAttendanceRecords(student.id)
}

// 加载未来排课
const loadUpcomingSchedules = async (studentId: number) => {
  loadingUpcoming.value = true
  try {
    const res = await getUpcomingSchedules(studentId, 14)  // 未来14天
    upcomingSchedules.value = res || []
  } catch {
    ElMessage.error('获取排课信息失败')
  } finally {
    loadingUpcoming.value = false
  }
}

// 加载出勤记录
const loadAttendanceRecords = async (studentId: number) => {
  loadingAttendances.value = true
  try {
    const res = await getStudentAttendances(studentId, { page_size: 50 })
    attendanceRecords.value = res.data?.items || []
  } catch {
    ElMessage.error('获取出勤记录失败')
  } finally {
    loadingAttendances.value = false
  }
}

// 显示请假表单
const showLeaveForm = (schedule: UpcomingScheduleItem) => {
  leaveForm.value = {
    schedule_id: schedule.schedule_id,
    schedule_date: schedule.schedule_date,
    start_time: schedule.start_time,
    end_time: schedule.end_time,
    class_plan_name: schedule.class_plan_name || '',
    leave_reason: '',
  }
  leaveFormVisible.value = true
}

// 提交请假
const submitLeave = async () => {
  if (!leaveForm.value.leave_reason.trim()) {
    ElMessage.warning('请输入请假原因')
    return
  }
  if (!attendanceStudent.value) return

  submittingLeave.value = true
  try {
    await applyLeaveForStudent(attendanceStudent.value.id, {
      schedule_id: leaveForm.value.schedule_id,
      leave_reason: leaveForm.value.leave_reason,
    })
    ElMessage.success('请假申请成功')
    leaveFormVisible.value = false
    // 刷新未来排课列表
    loadUpcomingSchedules(attendanceStudent.value.id)
    loadAttendanceRecords(attendanceStudent.value.id)
  } catch {
    ElMessage.error('请假申请失败')
  } finally {
    submittingLeave.value = false
  }
}

const loadDictionaries = async () => {
  try {
    const [genderRes, statusRes, gradeRes, sourceRes, subjectRes, studentLevelRes, learningGoalRes] = await Promise.all([
      getDictItems('gender'),
      getDictItems('student_status'),
      getDictItems('grade'),
      getDictItems('student_source'),
      getDictItems('subject'),
      getDictItems('student_level'),
      getDictItems('learning_goal'),
    ])
    genderOptions.value = genderRes || []
    statusOptions.value = statusRes || []
    gradeOptions.value = gradeRes || []
    sourceOptions.value = sourceRes || []
    subjectOptions.value = subjectRes || []
    studentLevelOptions.value = studentLevelRes || []
    learningGoalOptions.value = learningGoalRes || []
  } catch {
    // 字典加载失败不影响页面使用
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getStudents({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchKeyword.value || undefined,
      status: filterStatus.value || undefined,
      grade: filterGrade.value || undefined,
      source: filterSource.value || undefined,
    })
    students.value = res.data?.items || []
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
  filterGrade.value = ''
  filterSource.value = ''
  currentPage.value = 1
  loadData()
}

const showDialog = (item?: Student) => {
  editingItem.value = item || null
  if (item) {
    form.value = {
      name: item.name,
      phone: item.phone || '',
      gender: item.gender || '',
      birthday: item.birthday || '',
      grade: item.grade || '',
      school: item.school || '',
      parent_name: item.parent_name || '',
      parent_phone: item.parent_phone || '',
      address: item.address || '',
      source: item.source || '',
      subject_levels: item.subject_levels || [],
      learning_goals: item.learning_goals || [],
      status: item.status,
      remark: item.remark || '',
    }
  } else {
    form.value = {
      name: '',
      phone: '',
      gender: genderOptions.value[0]?.value || '',
      birthday: '',
      grade: '',
      school: '',
      parent_name: '',
      parent_phone: '',
      address: '',
      source: sourceOptions.value[0]?.value || '',
      subject_levels: [],
      learning_goals: [],
      status: 'active',
      remark: '',
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
      birthday: form.value.birthday || undefined,
      phone: form.value.phone || undefined,
      gender: form.value.gender || undefined,
      grade: form.value.grade || undefined,
      school: form.value.school || undefined,
      parent_name: form.value.parent_name || undefined,
      parent_phone: form.value.parent_phone || undefined,
      address: form.value.address || undefined,
      source: form.value.source || undefined,
      remark: form.value.remark || undefined,
      subject_levels: form.value.subject_levels?.length ? form.value.subject_levels : undefined,
      learning_goals: form.value.learning_goals?.length ? form.value.learning_goals : undefined,
    }
    if (editingItem.value) {
      await updateStudent(editingItem.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await createStudent(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

const handleDelete = async (id: number) => {
  await deleteStudent(id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => {
  loadDictionaries()
  loadData()
})
</script>

<style scoped lang="scss">
.student-view {
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

// 课时详情弹窗样式
.hours-detail {
  .hours-summary {
    display: flex;
    gap: 40px;
    padding: 16px;
    background: var(--bg-secondary);
    border-radius: 8px;
    margin-bottom: 16px;

    .summary-item {
      display: flex;
      flex-direction: column;
      gap: 4px;

      .label {
        font-size: 13px;
        color: var(--text-tertiary);
      }

      .value {
        font-size: 24px;
        font-weight: 600;
        color: var(--text-primary);

        &.price {
          color: var(--primary-500);
        }
      }
    }
  }
}

.hours-link {
  padding: 0;
}

// 科目水平标签样式
.subject-level-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;

  .subject-level-item {
    display: flex;
    align-items: center;
    gap: 8px;

    .subject-name {
      font-weight: 500;
      min-width: 32px;
    }
  }
}

// 出勤弹窗样式
.attendance-content {
  .loading-tip {
    text-align: center;
    padding: 20px;
    color: var(--text-tertiary);
  }

  .leave-reason-hint {
    font-size: 12px;
    color: var(--text-tertiary);
    cursor: help;
  }
}

// 学生详情弹窗样式
.student-detail {
  .detail-section {
    margin-top: 20px;

    h4 {
      margin: 0 0 12px;
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border-light);
    }
  }

  .tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .level-tag {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: var(--bg-secondary);
    border-radius: 6px;

    .subject {
      font-weight: 500;
      font-size: 14px;
    }
  }

  .remark-text {
    padding: 12px;
    background: var(--bg-secondary);
    border-radius: 6px;
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.6;
    white-space: pre-wrap;
  }
}
</style>
