<template>
  <div class="dashboard-container">
    <el-row justify="space-between" align="middle" class="header-row">
      <el-col :span="12">
        <h1>仪表盘</h1>
      </el-col>
      <el-col :span="12" style="text-align: right;">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          :shortcuts="shortcuts"
          @change="fetchDashboardData"
        />
      </el-col>
    </el-row>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="error" class="error-container">
      <el-alert title="加载失败" type="error" :description="error" show-icon />
    </div>

    <div v-else-if="dashboardData">
      <!-- Admin View -->
      <div v-if="dashboardData.role === 'admin'">
        <el-row :gutter="20" class="kpi-row">
          <el-col :span="6">
            <el-card>
              <el-statistic title="总排课时数" :value="dashboardData.stats.kpis.total_scheduled_hours" />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <el-statistic title="活跃教师数" :value="dashboardData.stats.kpis.active_teachers_count" />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <el-statistic title="上课学生人次" :value="dashboardData.stats.kpis.student_attendance_count" />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <el-statistic title="已完成课程数" :value="dashboardData.stats.kpis.completed_courses_count" />
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-card>
              <BaseChart :options="courseHoursOptions" />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <BaseChart :options="popularCoursesOptions" />
            </el-card>
          </el-col>
        </el-row>

        <el-row style="margin-top: 20px;">
            <el-col :span="24">
                <el-card>
                    <BaseChart :options="teacherWorkloadOptions" />
                </el-card>
            </el-col>
        </el-row>
      </div>

      <!-- Teacher View -->
      <div v-else-if="dashboardData.role === 'teacher'">
        <el-row :gutter="20" class="kpi-row">
          <el-col :span="8">
            <el-card>
              <el-statistic title="我的排课时数" :value="dashboardData.stats.kpis.total_hours" />
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card>
              <el-statistic title="我的课程数" :value="dashboardData.stats.kpis.course_count" />
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card>
              <el-statistic title="我的学生人次" :value="dashboardData.stats.kpis.student_count" />
            </el-card>
          </el-col>
        </el-row>

        <el-row>
          <el-col :span="24">
            <el-card>
              <BaseChart :options="subjectDistributionOptions" />
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- Student View -->
      <div v-else-if="dashboardData.role === 'student'">
        <el-row :gutter="20" class="kpi-row">
          <el-col :span="6">
            <el-card>
              <el-statistic title="我的课程数" :value="dashboardData.stats.kpis.course_count" />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <el-statistic title="我的上课时长 (小时)" :value="dashboardData.stats.kpis.total_hours" />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <el-statistic title="剩余总课时" :value="dashboardData.stats.kpis.remaining_lessons" />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <el-statistic title="出勤率 (%)" :value="dashboardData.stats.kpis.attendance_rate" />
            </el-card>
          </el-col>
        </el-row>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import apiClient from '@/api';
import dayjs from 'dayjs';
import BaseChart from '@/components/charts/BaseChart.vue';
import type { EChartsOption } from 'echarts';

const dateRange = ref<[Date, Date]>([
  dayjs().startOf('week').toDate(),
  dayjs().endOf('week').toDate(),
]);

const shortcuts = [
  {
    text: '本周',
    value: () => {
      const start = dayjs().startOf('week').toDate();
      const end = dayjs().endOf('week').toDate();
      return [start, end];
    },
  },
  {
    text: '本月',
    value: () => {
      const start = dayjs().startOf('month').toDate();
      const end = dayjs().endOf('month').toDate();
      return [start, end];
    },
  },
  {
    text: '上个月',
    value: () => {
      const start = dayjs().subtract(1, 'month').startOf('month').toDate();
      const end = dayjs().subtract(1, 'month').endOf('month').toDate();
      return [start, end];
    },
  },
];

const loading = ref(true);
const error = ref<string | null>(null);
const dashboardData = ref<any>(null);

const fetchDashboardData = async () => {
  if (!dateRange.value) return;

  loading.value = true;
  error.value = null;
  dashboardData.value = null;

  try {
    const [startDate, endDate] = dateRange.value;
    const params = {
      start_date: dayjs(startDate).format('YYYY-MM-DD'),
      end_date: dayjs(endDate).format('YYYY-MM-DD'),
    };
    const response = await apiClient.get('/dashboard/stats/', { params });
    dashboardData.value = response.data;
  } catch (e: any) {
    error.value = e.message || '获取数据失败';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchDashboardData();
});

// Chart Options
const courseHoursOptions = computed<EChartsOption>(() => {
  const chartData = dashboardData.value?.stats?.charts?.course_hours_distribution || [];
  return {
    title: { text: '课程时数分布' },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: chartData.map((item: any) => item.date),
    },
    yAxis: { type: 'value', name: '小时' },
    series: [{
      data: chartData.map((item: any) => item.hours),
      type: 'bar',
    }],
  };
});

const popularCoursesOptions = computed<EChartsOption>(() => {
  const chartData = dashboardData.value?.stats?.charts?.popular_courses || [];
  return {
    title: { text: '热门课程产品', left: 'center' },
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
    series: [{
      type: 'pie',
      radius: '50%',
      data: chartData.map((item: any) => ({ value: item.entry_count, name: item.course_name })),
    }],
  };
});

const teacherWorkloadOptions = computed<EChartsOption>(() => {
    const chartData = dashboardData.value?.stats?.charts?.teacher_workload || [];
    return {
        title: { text: '教师工作量排行 (Top 10)' },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'value', boundaryGap: [0, 0.01] },
        yAxis: {
            type: 'category',
            data: chartData.map((item: any) => item.teacher_name).reverse(),
        },
        series: [{
            name: '工作小时数',
            type: 'bar',
            data: chartData.map((item: any) => item.hours).reverse(),
        }],
    };
});

const subjectDistributionOptions = computed<EChartsOption>(() => {
  const chartData = dashboardData.value?.stats?.charts?.subject_distribution || [];
  return {
    title: { text: '我的授课科目分布', left: 'center' },
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
    series: [{
      type: 'pie',
      radius: '50%',
      data: chartData.map((item: any) => ({ value: item.course_count, name: item.subject_name })),
    }],
  };
});
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}
.header-row {
  margin-bottom: 20px;
}
.kpi-row {
  margin-bottom: 20px;
}
</style>
