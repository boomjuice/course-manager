<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Calendar, User, UserFilled, Reading, Notebook, DataLine } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  getDashboardStats,
  getChartData,
  type DashboardStats,
  type ChartDataResponse
} from '@/api/dashboard'
import * as echarts from 'echarts'

const authStore = useAuthStore()
const currentUser = computed(() => authStore.currentUser)

const stats = ref<DashboardStats | null>(null)
const chartData = ref<ChartDataResponse | null>(null)
const loading = ref(false)
const chartLoading = ref(false)

// ECharts实例
const trendChartRef = ref<HTMLDivElement | null>(null)
const classStatChartRef = ref<HTMLDivElement | null>(null)
let trendChart: echarts.ECharts | null = null
let classStatChart: echarts.ECharts | null = null

const getRoleText = (role: string | undefined) => {
  const map: Record<string, string> = {
    admin: '管理员',
    teacher: '教师',
    student: '学生'
  }
  return map[role || ''] || '未知'
}

const loadStats = async () => {
  loading.value = true
  try {
    const res = await getDashboardStats()
    stats.value = res || null
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

const loadChartData = async () => {
  chartLoading.value = true
  try {
    const res = await getChartData(30)
    chartData.value = res || null
    await nextTick()
    renderCharts()
  } catch {
    // ignore
  } finally {
    chartLoading.value = false
  }
}

// 渲染报名趋势图表
const renderTrendChart = () => {
  if (!trendChartRef.value || !chartData.value) return

  if (trendChart) {
    trendChart.dispose()
  }

  trendChart = echarts.init(trendChartRef.value)
  const data = chartData.value.enrollment_trend

  const option: echarts.EChartsOption = {
    title: {
      text: '近30天报名趋势',
      left: 'center',
      textStyle: { fontSize: 14, fontWeight: 500 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['报名人数', '报名金额'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map(d => d.date.slice(5)), // 只显示月-日
      axisLabel: {
        rotate: 45,
        fontSize: 10
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '人数',
        position: 'left',
        axisLine: { show: true, lineStyle: { color: '#5470c6' } },
        splitLine: { lineStyle: { type: 'dashed' } }
      },
      {
        type: 'value',
        name: '金额(元)',
        position: 'right',
        axisLine: { show: true, lineStyle: { color: '#91cc75' } },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '报名人数',
        type: 'line',
        smooth: true,
        data: data.map(d => d.count),
        itemStyle: { color: '#5470c6' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(84, 112, 198, 0.3)' },
            { offset: 1, color: 'rgba(84, 112, 198, 0.05)' }
          ])
        }
      },
      {
        name: '报名金额',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: data.map(d => d.amount),
        itemStyle: { color: '#91cc75' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(145, 204, 117, 0.3)' },
            { offset: 1, color: 'rgba(145, 204, 117, 0.05)' }
          ])
        }
      }
    ]
  }

  trendChart.setOption(option)
}

// 渲染班级报名统计图表
const renderClassStatChart = () => {
  if (!classStatChartRef.value || !chartData.value) return

  if (classStatChart) {
    classStatChart.dispose()
  }

  classStatChart = echarts.init(classStatChartRef.value)
  const data = chartData.value.class_plan_stats

  if (data.length === 0) {
    // 没有数据时显示提示
    classStatChart.setOption({
      title: {
        text: '班级报名统计 (Top 10)',
        left: 'center',
        textStyle: { fontSize: 14, fontWeight: 500 }
      },
      graphic: {
        type: 'text',
        left: 'center',
        top: 'middle',
        style: {
          text: '暂无数据',
          fontSize: 14,
          fill: '#999'
        }
      }
    })
    return
  }

  const option: echarts.EChartsOption = {
    title: {
      text: '班级报名统计 (Top 10)',
      left: 'center',
      textStyle: { fontSize: 14, fontWeight: 500 }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const item = params[0]
        const stat = data[item.dataIndex]
        if (!stat) return ''
        return `${stat.class_plan_name}<br/>
                报名人数: ${stat.enrollment_count}<br/>
                报名金额: ¥${stat.total_amount.toLocaleString()}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.class_plan_name.length > 8 ? d.class_plan_name.slice(0, 8) + '...' : d.class_plan_name),
      axisLabel: {
        rotate: 30,
        fontSize: 10
      }
    },
    yAxis: {
      type: 'value',
      name: '报名人数'
    },
    series: [
      {
        type: 'bar',
        data: data.map(d => d.enrollment_count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#667eea' },
            { offset: 1, color: '#764ba2' }
          ]),
          borderRadius: [4, 4, 0, 0]
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#764ba2' },
              { offset: 1, color: '#667eea' }
            ])
          }
        }
      }
    ]
  }

  classStatChart.setOption(option)
}

// 渲染所有图表
const renderCharts = () => {
  renderTrendChart()
  renderClassStatChart()
}

// 窗口resize时重新调整图表大小
const handleResize = () => {
  trendChart?.resize()
  classStatChart?.resize()
}

onMounted(() => {
  loadStats()
  loadChartData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  classStatChart?.dispose()
})
</script>

<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>仪表盘</h1>
    </div>

    <div class="welcome-card card">
      <div class="card-body">
        <h2>欢迎回来，{{ currentUser?.username }}！</h2>
        <p>您当前的角色是：<el-tag>{{ getRoleText(currentUser?.role) }}</el-tag></p>
      </div>
    </div>

    <el-row :gutter="20" class="mt-lg" v-loading="loading">
      <el-col :span="6">
        <div class="stat-card card">
          <div class="card-body">
            <div class="stat-icon" style="background: var(--primary-100); color: var(--primary-600);">
              <el-icon :size="24"><User /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">在读学生</p>
              <p class="stat-value">{{ stats?.active_students ?? '--' }}</p>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card card">
          <div class="card-body">
            <div class="stat-icon" style="background: var(--success-light); color: var(--success);">
              <el-icon :size="24"><UserFilled /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">授课教师</p>
              <p class="stat-value">{{ stats?.total_teachers ?? '--' }}</p>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card card">
          <div class="card-body">
            <div class="stat-icon" style="background: var(--warning-light); color: var(--warning);">
              <el-icon :size="24"><Reading /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">进行中班级</p>
              <p class="stat-value">{{ stats?.active_class_plans ?? '--' }}</p>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card card">
          <div class="card-body">
            <div class="stat-icon" style="background: var(--info-light); color: var(--info);">
              <el-icon :size="24"><Notebook /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">课程产品</p>
              <p class="stat-value">{{ stats?.total_courses ?? '--' }}</p>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-lg">
      <el-col :span="12">
        <div class="stat-card card">
          <div class="card-body">
            <div class="stat-icon" style="background: #e0f2fe; color: #0284c7;">
              <el-icon :size="24"><Calendar /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">总报名数</p>
              <p class="stat-value">{{ stats?.total_enrollments ?? '--' }}</p>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="stat-card card">
          <div class="card-body">
            <div class="stat-icon" style="background: #fce7f3; color: #db2777;">
              <el-icon :size="24"><DataLine /></el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-label">近7天新增报名</p>
              <p class="stat-value">{{ stats?.recent_enrollments ?? '--' }}</p>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="mt-lg" v-loading="chartLoading">
      <el-col :span="14">
        <el-card>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card>
          <div ref="classStatChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Quick Links -->
    <el-card class="mt-lg">
      <template #header>
        <div class="quick-links-header">
          <span>快捷入口</span>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col :span="4">
          <router-link to="/students" class="quick-link">
            <el-icon :size="32" color="var(--primary-500)"><User /></el-icon>
            <span>学生管理</span>
          </router-link>
        </el-col>
        <el-col :span="4">
          <router-link to="/teachers" class="quick-link">
            <el-icon :size="32" color="var(--success)"><UserFilled /></el-icon>
            <span>教师管理</span>
          </router-link>
        </el-col>
        <el-col :span="4">
          <router-link to="/courses/offerings" class="quick-link">
            <el-icon :size="32" color="var(--warning)"><Reading /></el-icon>
            <span>开班管理</span>
          </router-link>
        </el-col>
        <el-col :span="4">
          <router-link to="/enrollments" class="quick-link">
            <el-icon :size="32" color="var(--info)"><Calendar /></el-icon>
            <span>报名管理</span>
          </router-link>
        </el-col>
        <el-col :span="4">
          <router-link to="/courses/products" class="quick-link">
            <el-icon :size="32" color="#7c3aed"><Notebook /></el-icon>
            <span>课程产品</span>
          </router-link>
        </el-col>
        <el-col :span="4">
          <router-link to="/settings/profile" class="quick-link">
            <el-icon :size="32" color="#6b7280"><DataLine /></el-icon>
            <span>个人设置</span>
          </router-link>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.dashboard {
  padding: 20px;

  .page-header {
    margin-bottom: 20px;
    h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
    }
  }

  .welcome-card {
    h2 {
      font-size: 20px;
      font-weight: 600;
      margin-bottom: var(--spacing-sm);
    }
    p {
      color: var(--text-secondary);
    }
  }

  .stat-card {
    .card-body {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
    }

    .stat-icon {
      width: 56px;
      height: 56px;
      border-radius: var(--radius-lg);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .stat-info {
      .stat-label {
        font-size: 14px;
        color: var(--text-tertiary);
        margin-bottom: 4px;
      }
      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: var(--text-primary);
      }
    }
  }

  .quick-links-header {
    font-weight: 600;
  }

  .quick-link {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 16px;
    border-radius: 8px;
    text-decoration: none;
    color: var(--text-primary);
    transition: background-color 0.2s;

    &:hover {
      background-color: var(--el-fill-color-light);
    }

    span {
      font-size: 14px;
    }
  }

  .mt-lg {
    margin-top: 20px;
  }

  .chart-container {
    width: 100%;
    height: 320px;
  }
}
</style>
