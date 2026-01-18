<template>
  <div class="system-settings">
    <h2>系统管理</h2>

    <!-- 定时任务管理 -->
    <el-card class="section-card">
      <template #header>
        <div class="card-header">
          <span>定时任务</span>
          <el-tag :type="schedulerStatus?.running ? 'success' : 'danger'" size="small">
            {{ schedulerStatus?.running ? '运行中' : '已停止' }}
          </el-tag>
        </div>
      </template>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        <template #title>
          <span>定时任务说明</span>
        </template>
        <template #default>
          <div class="alert-content">
            <p><strong>自动完成排课</strong>：每天凌晨2:00自动将过期的排课（昨天及之前）标记为已完成，并为报名学生扣除相应课时。</p>
            <p><strong>自动结班</strong>：每天凌晨2:05自动将结班日期已过的班级标记为已结班。</p>
            <p style="color: #e6a23c; margin-top: 8px;">⚠️ 如果服务器在凌晨2点未运行，任务不会自动补执行。可以点击下方按钮手动触发。</p>
          </div>
        </template>
      </el-alert>

      <el-table :data="schedulerStatus?.jobs || []" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="任务名称" min-width="200" />
        <el-table-column label="执行周期" width="160">
          <template #default="{ row }">
            {{ formatTrigger(row.trigger) }}
          </template>
        </el-table-column>
        <el-table-column label="下次执行时间" width="200">
          <template #default="{ row }">
            {{ row.next_run_time ? formatDateTime(row.next_run_time) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :loading="runningTask === row.id"
              @click="handleRunTask(row)"
            >
              立即执行
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSchedulerStatus, runSchedulerTask, type SchedulerStatus } from '@/api/scheduler'

const loading = ref(false)
const runningTask = ref<string | null>(null)
const schedulerStatus = ref<SchedulerStatus | null>(null)

const loadSchedulerStatus = async () => {
  loading.value = true
  try {
    const res = await getSchedulerStatus()
    schedulerStatus.value = res || null
  } catch {
    // 权限不足等错误已由拦截器处理
  } finally {
    loading.value = false
  }
}

const handleRunTask = async (job: { id: string; name: string }) => {
  try {
    await ElMessageBox.confirm(
      `确定要立即执行「${job.name}」吗？`,
      '确认执行',
      { type: 'warning' }
    )

    runningTask.value = job.id
    await runSchedulerTask(job.id)
    ElMessage.success(`任务「${job.name}」执行完成`)
    // 刷新状态
    await loadSchedulerStatus()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('任务执行失败')
    }
  } finally {
    runningTask.value = null
  }
}

const formatDateTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 把cron表达式转成中文
const formatTrigger = (trigger: string) => {
  // 解析 cron[hour='2', minute='0'] 这种格式
  const hourMatch = trigger.match(/hour='(\d+)'/)
  const minuteMatch = trigger.match(/minute='(\d+)'/)

  if (hourMatch?.[1] && minuteMatch?.[1]) {
    const hour = hourMatch[1].padStart(2, '0')
    const minute = minuteMatch[1].padStart(2, '0')
    return `每天 ${hour}:${minute}`
  }

  // 其他格式直接返回
  return trigger
}

onMounted(() => {
  loadSchedulerStatus()
})
</script>

<style scoped lang="scss">
.system-settings {
  padding: 20px;

  h2 {
    margin: 0 0 20px;
    font-size: 20px;
    font-weight: 600;
  }
}

.section-card {
  margin-bottom: 20px;

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: 600;
  }
}

.alert-content {
  p {
    margin: 4px 0;
    font-size: 13px;
    line-height: 1.6;
  }
}
</style>
