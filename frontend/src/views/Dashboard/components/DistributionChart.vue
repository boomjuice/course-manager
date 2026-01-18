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

interface DistributionItem {
  name: string
  value: number
  color?: string
}

const props = defineProps<{
  title: string
  data: DistributionItem[]
  type?: 'pie' | 'ring'  // 饼图或环形图
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
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [{
      type: 'pie',
      radius: props.type === 'ring' ? ['40%', '70%'] : '70%',
      center: ['60%', '50%'],
      data: props.data.map(d => ({
        name: d.name,
        value: d.value,
        itemStyle: d.color ? { color: d.color } : undefined
      })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: {
        formatter: '{b}: {d}%'
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
