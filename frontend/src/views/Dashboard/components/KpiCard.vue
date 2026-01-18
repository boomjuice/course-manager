<template>
  <el-card shadow="hover" class="kpi-card">
    <div class="kpi-content">
      <div class="kpi-label">{{ label }}</div>
      <div class="kpi-value">
        <span class="value">{{ formattedValue }}</span>
        <span v-if="unit" class="unit">{{ unit }}</span>
      </div>
      <div v-if="trend !== undefined" class="kpi-trend" :class="trendClass">
        <el-icon v-if="trend > 0"><ArrowUp /></el-icon>
        <el-icon v-else-if="trend < 0"><ArrowDown /></el-icon>
        <span>{{ Math.abs(trend) }}%</span>
      </div>
      <div v-if="isTimeFiltered" class="time-badge">
        <el-icon><Clock /></el-icon>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowUp, ArrowDown, Clock } from '@element-plus/icons-vue'

const props = defineProps<{
  label: string
  value: number | string
  unit?: string
  trend?: number
  isTimeFiltered?: boolean
}>()

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    return props.value.toLocaleString()
  }
  return props.value
})

const trendClass = computed(() => ({
  'trend-up': props.trend && props.trend > 0,
  'trend-down': props.trend && props.trend < 0
}))
</script>

<style scoped>
.kpi-card {
  height: 120px;
}
.kpi-content {
  position: relative;
}
.kpi-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}
.kpi-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}
.kpi-value .unit {
  font-size: 14px;
  color: #909399;
  margin-left: 4px;
}
.kpi-trend {
  margin-top: 8px;
  font-size: 12px;
}
.trend-up {
  color: #67c23a;
}
.trend-down {
  color: #f56c6c;
}
.time-badge {
  position: absolute;
  top: 0;
  right: 0;
  color: #409eff;
  font-size: 12px;
}
</style>
