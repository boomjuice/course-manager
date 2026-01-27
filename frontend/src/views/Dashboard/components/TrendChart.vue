<template>
  <el-card shadow="hover">
    <template #header>
      <div class="chart-header">
        <span>{{ title }}</span>
      </div>
    </template>
    <div ref="chartRef" class="chart-container"></div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

interface TrendDataPoint {
  date: string
  value: number
  label?: string
}

const props = defineProps<{
  title: string
  data: TrendDataPoint[]
  yAxisName?: string
  color?: string
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const initChart = () => {
  if (!chartRef.value) return

  chart = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chart) return

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: props.data.map(d => d.date),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: props.yAxisName
    },
    series: [{
      type: 'line',
      data: props.data.map(d => d.value),
      smooth: true,
      areaStyle: {
        opacity: 0.3
      },
      itemStyle: {
        color: props.color || '#409eff'
      }
    }]
  }

  chart.setOption(option)
}

watch(() => props.data, updateChart, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  chart?.dispose()
})
</script>

<style scoped>
.chart-header {
  font-weight: 600;
}
.chart-container {
  height: 300px;
}
</style>
