<!-- frontend/src/views/Dashboard/AdminDashboard.vue -->
<template>
  <div class="admin-dashboard">
    <!-- 时间选择器和校区选择器（超管专属） -->
    <div class="dashboard-toolbar">
      <TimeRangeSelector @change="handleTimeRangeChange" @refresh="refreshCurrentTab" />
      <el-select
        v-if="isSuperAdmin"
        v-model="selectedCampusId"
        placeholder="全部校区"
        clearable
        @change="handleCampusChange"
        class="campus-selector"
      >
        <el-option
          v-for="campus in campusList"
          :key="campus.id"
          :label="campus.name"
          :value="campus.id"
        />
      </el-select>
    </div>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="概览" name="overview">
        <div class="tab-content" v-loading="overviewLoading">
          <el-row :gutter="20" class="kpi-row">
            <el-col :span="6" v-for="kpi in overviewData?.kpi_cards" :key="kpi.label">
              <KpiCard
                :label="kpi.label"
                :value="kpi.value"
                :unit="kpi.unit"
                :trend="kpi.trend"
                :is-time-filtered="kpi.is_time_filtered"
              />
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="12">
              <TrendChart
                v-if="overviewData?.enrollment_trend?.length"
                title="报名趋势"
                :data="overviewData.enrollment_trend"
                y-axis-name="报名数"
                color="#67c23a"
              />
            </el-col>
            <el-col :span="12">
              <TrendChart
                v-if="overviewData?.revenue_trend?.length"
                title="收入趋势"
                :data="overviewData.revenue_trend"
                y-axis-name="金额"
                color="#e6a23c"
              />
            </el-col>
          </el-row>

          <!-- 校区对比（超管专属） -->
          <el-row v-if="overviewData?.campus_comparison" :gutter="20" class="comparison-row">
            <el-col :span="24">
              <DistributionChart
                title="校区对比"
                :data="overviewData.campus_comparison"
                type="pie"
              />
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <el-tab-pane label="学生" name="students">
        <div class="tab-content" v-loading="studentsLoading">
          <!-- KPI 卡片 -->
          <el-row :gutter="20" class="kpi-row">
            <el-col :span="6" v-for="kpi in studentsData?.kpi_cards" :key="kpi.label">
              <KpiCard
                :label="kpi.label"
                :value="kpi.value"
                :unit="kpi.unit"
                :trend="kpi.trend"
                :is-time-filtered="kpi.is_time_filtered"
              />
            </el-col>
          </el-row>

          <!-- 分布图区域 -->
          <el-row :gutter="20">
            <el-col :span="8">
              <DistributionChart
                v-if="studentsData?.status_distribution?.length"
                title="学生状态分布"
                :data="studentsData.status_distribution"
                type="ring"
              />
            </el-col>
            <el-col :span="8">
              <DistributionChart
                v-if="studentsData?.source_distribution?.length"
                title="学生来源分布"
                :data="studentsData.source_distribution"
                type="pie"
              />
            </el-col>
            <el-col :span="8">
              <DistributionChart
                v-if="studentsData?.grade_distribution?.length"
                title="年级分布"
                :data="studentsData.grade_distribution"
                type="pie"
              />
            </el-col>
          </el-row>

          <!-- 趋势图 -->
          <el-row :gutter="20" class="trend-row">
            <el-col :span="24">
              <TrendChart
                v-if="studentsData?.new_student_trend?.length"
                title="新增学生趋势"
                :data="studentsData.new_student_trend"
                y-axis-name="人数"
                color="#67c23a"
              />
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <el-tab-pane label="教师" name="teachers">
        <div class="tab-content">
          <el-empty description="教师分析（待实现）" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="班级" name="classes">
        <div class="tab-content">
          <el-empty description="班级分析（待实现）" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="财务" name="finance">
        <div class="tab-content">
          <el-empty description="财务分析（待实现）" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getAdminDashboard, getAdminStudents } from '@/api/dashboard'
import type { AdminDashboardOverview, AdminDashboardStudents, TimeRangeParams } from '@/api/dashboard'
import KpiCard from './components/KpiCard.vue'
import TimeRangeSelector from './components/TimeRangeSelector.vue'
import TrendChart from './components/TrendChart.vue'
import DistributionChart from './components/DistributionChart.vue'

const authStore = useAuthStore()

const activeTab = ref('overview')
const overviewData = ref<AdminDashboardOverview | null>(null)
const studentsData = ref<AdminDashboardStudents | null>(null)
const timeRange = ref<TimeRangeParams>({})
const selectedCampusId = ref<number | null>(null)
const campusList = ref<Array<{ id: number; name: string }>>([])

const overviewLoading = ref(false)
const studentsLoading = ref(false)

// 判断是否为超级管理员（可跨校区查看数据）
const isSuperAdmin = computed(() => {
  // 超级管理员没有绑定校区，可以切换查看所有校区
  return authStore.currentCampusId === null && authStore.isAdmin
})

const getParams = (): TimeRangeParams => ({
  ...timeRange.value,
  campus_id: selectedCampusId.value || undefined
})

const loadOverview = async () => {
  overviewLoading.value = true
  try {
    overviewData.value = await getAdminDashboard(getParams()) ?? null
  } catch (e) {
    console.error('Failed to load overview', e)
  } finally {
    overviewLoading.value = false
  }
}

const loadStudents = async () => {
  studentsLoading.value = true
  try {
    studentsData.value = await getAdminStudents(getParams()) ?? null
  } catch (e) {
    console.error('Failed to load students', e)
  } finally {
    studentsLoading.value = false
  }
}

const handleTabChange = (tab: string) => {
  if (tab === 'overview') loadOverview()
  if (tab === 'students') loadStudents()
  // 其他 Tab 待实现
}

const handleTimeRangeChange = (range: { startDate: string; endDate: string }) => {
  timeRange.value = { start_date: range.startDate, end_date: range.endDate }
  refreshCurrentTab()
}

const handleCampusChange = () => {
  refreshCurrentTab()
}

const refreshCurrentTab = () => {
  if (activeTab.value === 'overview') loadOverview()
  if (activeTab.value === 'students') loadStudents()
  // 其他 Tab 待实现
}

// TODO: 加载校区列表
const loadCampusList = async () => {
  // 从可用校区列表获取（如果是超管，登录时会返回所有校区）
  if (authStore.availableCampuses.length > 0) {
    campusList.value = authStore.availableCampuses
  }
  // 或者从 API 获取校区列表
  // campusList.value = await getCampusList()
}

onMounted(() => {
  loadOverview()
  if (isSuperAdmin.value) {
    loadCampusList()
  }
})
</script>

<style scoped>
.admin-dashboard {
  background: #f5f7fa;
  min-height: 100%;
}
.dashboard-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: #fff;
  border-radius: 4px;
}
.campus-selector {
  width: 200px;
}
.tab-content {
  padding: 20px 0;
}
.kpi-row {
  margin-bottom: 20px;
}
.comparison-row {
  margin-top: 20px;
}
.trend-row {
  margin-top: 20px;
}
</style>
