<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>数据字典管理</span>
        <el-button type="primary" @click="handleAdd">新建条目</el-button>
      </div>
    </template>

    <!-- 筛选/搜索区 -->
    <el-form :inline="true" :model="filters" @submit.prevent="fetchData">
      <el-form-item label="分组代码">
        <el-select v-model="filters.group_code" style="width: 150px" placeholder="按分组筛选"
                   clearable @change="fetchData">
          <el-option v-for="group in groupCodeOptions" :key="group" :label="group" :value="group"/>
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetchData">查询</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
    <el-table :data="tableData" v-loading="loading" style="width: 100%">
      <el-table-column prop="group_code" label="分组代码"/>
      <el-table-column prop="subgroup" label="子分组"/>
      <el-table-column prop="item_value" label="显示值"/>
      <el-table-column prop="sort_order" label="排序"/>
      <el-table-column prop="created_by" label="创建人" width="120" />
      <el-table-column label="创建时间" width="180">
        <template #default="scope">{{ formatTime(scope.row.created_time) }}</template>
      </el-table-column>
      <el-table-column prop="updated_by" label="修改人" width="120" />
      <el-table-column label="修改时间" width="180">
        <template #default="scope">{{ formatTime(scope.row.updated_time) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="scope">
          <el-button link type="primary" size="small" @click="handleEdit(scope.row)">编辑
          </el-button>
          <el-button link type="danger" size="small" @click="handleDelete(scope.row)">删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      class="pagination"
      background
      layout="prev, pager, next, total"
      :total="total"
      :page-size="pageSize"
      @current-change="handlePageChange"
    />
  </el-card>

  <!-- 新增/编辑弹窗 -->
  <DataDictionaryForm
    v-model:visible="dialogVisible"
    :item-data="selectedItem"
    :group-code-options="groupCodeOptions"
    @success="onFormSuccess"
  />
</template>

<script lang="ts" setup>
import {ref, onMounted, reactive, nextTick} from 'vue';
import apiClient from '@/api';
import {ElMessage, ElMessageBox} from 'element-plus';
import DataDictionaryForm from '@/components/DataDictionaryForm.vue';
import {formatTime} from "@/utils/format.ts";

// --- state ---
const tableData = ref([]);
const loading = ref(false);
const total = ref(0);
const pageSize = ref(20);
const currentPage = ref(1);

const filters = reactive({
  group_code: '', // Start with empty
});

const groupCodeOptions = ref<string[]>([]);
const dialogVisible = ref(false);
const selectedItem = ref(null);

// --- methods ---
const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      group_code: filters.group_code || undefined,
    };
    const response = await apiClient.get('/data-dictionary/', {params});
    tableData.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("Failed to fetch data dictionary:", error);
  } finally {
    loading.value = false;
  }
};

const fetchGroupCodes = async () => {
  try {
    const response = await apiClient.get('/data-dictionary/', {params: {page_size: 1000}});
    const allItems = response.data.results;
    const uniqueGroups = new Set(allItems.map((item: any) => item.group_code));
    groupCodeOptions.value = Array.from(uniqueGroups);

    await nextTick();

    if (groupCodeOptions.value.includes('grades')) {
      filters.group_code = 'grades';
    }
    await fetchData();
  } catch (error) {
    console.error("Failed to fetch group codes:", error);
    await fetchData();
  }
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchData();
};

const handleAdd = () => {
  selectedItem.value = null;
  dialogVisible.value = true;
};

const handleEdit = (row: any) => {
  selectedItem.value = row;
  dialogVisible.value = true;
};

const onFormSuccess = async (newData: any) => {
  ElMessage.success('操作成功');
  // If a new group was potentially added, update the options
  if (!groupCodeOptions.value.includes(newData.group_code)) {
    groupCodeOptions.value.push(newData.group_code);
  }
  // Only refresh the table data
  await fetchData();
};

const handleDelete = (row: any) => {
  ElMessageBox.confirm(
    `确定要删除条目 "${row.item_value}" 吗？`,
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await apiClient.delete(`/data-dictionary/${row.id}/`);
      ElMessage.success('删除成功');
      await fetchData(); // Only refresh the table data
      // Optionally, you could re-fetch group codes if the deleted item was the last of its group
    } catch (error) {
      console.error('Failed to delete item:', error);
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
};

// --- lifecycle ---
onMounted(() => {
  fetchGroupCodes();
});
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
