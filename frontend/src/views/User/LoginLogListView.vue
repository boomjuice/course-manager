<template>
  <div class="login-log-view">
    <div class="page-header">
      <h1>登录日志</h1>
    </div>

    <!-- Search Bar -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索用户名/IP..."
        clearable
        style="width: 200px"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 120px">
        <el-option label="成功" value="success" />
        <el-option label="失败" value="failed" />
      </el-select>
      <el-select v-model="filterUser" placeholder="用户" clearable filterable style="width: 150px">
        <el-option
          v-for="u in allUsers"
          :key="u.id"
          :label="u.username"
          :value="u.id"
        />
      </el-select>
      <el-button @click="handleSearch">搜索</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- Table -->
    <el-table :data="logs" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="login_time" label="登录时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.login_time) }}
        </template>
      </el-table-column>
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="ip_address" label="IP地址" width="140" />
      <el-table-column prop="status" label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
            {{ row.status === 'success' ? '成功' : '失败' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="fail_reason" label="失败原因" min-width="150">
        <template #default="{ row }">
          {{ row.fail_reason || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="user_agent" label="浏览器" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          {{ parseUserAgent(row.user_agent) }}
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadData"
        @current-change="loadData"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getLoginLogs, getUsers, type LoginLog, type User } from '@/api/user'

// State
const logs = ref<LoginLog[]>([])
const allUsers = ref<User[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const filterStatus = ref('')
const filterUser = ref<number | undefined>(undefined)

// Methods
const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const parseUserAgent = (ua?: string) => {
  if (!ua) return '-'
  // Simple UA parsing
  if (ua.includes('Chrome')) return 'Chrome'
  if (ua.includes('Firefox')) return 'Firefox'
  if (ua.includes('Safari')) return 'Safari'
  if (ua.includes('Edge')) return 'Edge'
  if (ua.includes('MSIE') || ua.includes('Trident')) return 'IE'
  return ua.length > 50 ? ua.substring(0, 50) + '...' : ua
}

const loadUsers = async () => {
  try {
    const res = await getUsers({ page_size: 1000 })
    allUsers.value = res.data?.items || []
  } catch {
    // ignore
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getLoginLogs({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchKeyword.value || undefined,
      status: filterStatus.value || undefined,
      user_id: filterUser.value,
    })
    logs.value = res.data?.items || []
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
  filterUser.value = undefined
  currentPage.value = 1
  loadData()
}

onMounted(() => {
  loadUsers()
  loadData()
})
</script>

<style scoped lang="scss">
.login-log-view {
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
</style>
