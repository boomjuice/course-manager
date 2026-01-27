<template>
  <div class="time-range-selector">
    <el-radio-group v-model="selectedPreset" @change="handlePresetChange">
      <el-radio-button label="today">今日</el-radio-button>
      <el-radio-button label="week">本周</el-radio-button>
      <el-radio-button label="month">本月</el-radio-button>
      <el-radio-button label="7days">近7天</el-radio-button>
      <el-radio-button label="30days">近30天</el-radio-button>
      <el-radio-button label="90days">近90天</el-radio-button>
      <el-radio-button label="custom">自定义</el-radio-button>
    </el-radio-group>

    <el-date-picker
      v-if="selectedPreset === 'custom'"
      v-model="customRange"
      type="daterange"
      range-separator="至"
      start-placeholder="开始日期"
      end-placeholder="结束日期"
      @change="handleCustomChange"
      class="custom-picker"
    />

    <el-button :icon="Refresh" circle @click="handleRefresh" class="refresh-btn" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'

const emit = defineEmits<{
  (e: 'change', range: { startDate: string; endDate: string }): void
  (e: 'refresh'): void
}>()

const selectedPreset = ref('30days')
const customRange = ref<[Date, Date] | null>(null)

// 格式化日期为 YYYY-MM-DD 格式
const formatDate = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const getDateRange = (preset: string): { startDate: string; endDate: string } => {
  const today = new Date()
  const endDate = formatDate(today)
  let startDate: string

  switch (preset) {
    case 'today':
      startDate = endDate
      break
    case 'week': {
      const weekStart = new Date(today)
      weekStart.setDate(today.getDate() - today.getDay() + 1)
      startDate = formatDate(weekStart)
      break
    }
    case 'month': {
      const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
      startDate = formatDate(monthStart)
      break
    }
    case '7days': {
      const d = new Date(today)
      d.setDate(d.getDate() - 6)
      startDate = formatDate(d)
      break
    }
    case '30days': {
      const d = new Date(today)
      d.setDate(d.getDate() - 29)
      startDate = formatDate(d)
      break
    }
    case '90days': {
      const d = new Date(today)
      d.setDate(d.getDate() - 89)
      startDate = formatDate(d)
      break
    }
    default:
      startDate = endDate
  }

  return { startDate, endDate }
}

const handlePresetChange = (preset: string) => {
  if (preset !== 'custom') {
    emit('change', getDateRange(preset))
  }
}

const handleCustomChange = (range: [Date, Date] | null) => {
  if (range) {
    emit('change', {
      startDate: formatDate(range[0]),
      endDate: formatDate(range[1])
    })
  }
}

const handleRefresh = () => {
  emit('refresh')
}

// 初始化时触发一次
handlePresetChange(selectedPreset.value)
</script>

<style scoped>
.time-range-selector {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.custom-picker {
  width: 260px;
}
.refresh-btn {
  margin-left: auto;
}
</style>
