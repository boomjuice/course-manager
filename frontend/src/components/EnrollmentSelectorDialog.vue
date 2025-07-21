<template>
  <el-dialog
    :model-value="visible"
    title="选择报名记录"
    width="800px"
    @close="handleClose"
  >
    <!-- 筛选/搜索区 -->
    <el-form :inline="true" :model="filters" @submit.prevent="fetchData(1)">
      <el-form-item label="学生">
        <el-input v-model="filters.student_name" placeholder="按学生姓名搜索" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetchData(1)">查询</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
    <el-table
      ref="tableRef"
      :data="tableData"
      v-loading="loading"
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="display_name" label="报名记录" />
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
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleConfirm">确定</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, reactive, watch } from 'vue';
import apiClient from '@/api';

const props = defineProps<{
  visible: boolean;
  selectedIds: number[];
  courseOfferingId?: number;
}>();

const emit = defineEmits(['update:visible', 'confirm']);

const tableData = ref([]);
const loading = ref(false);
const total = ref(0);
const pageSize = ref(10);
const currentPage = ref(1);
const multipleSelection = ref([]);

const filters = reactive({
  student_name: '',
});

const fetchData = async (page = 1) => {
  if (!props.courseOfferingId) {
    tableData.value = [];
    total.value = 0;
    return;
  }
  loading.value = true;
  currentPage.value = page;
  try {
    const params = { 
      page: currentPage.value,
      course_offering: props.courseOfferingId,
      student__name__icontains: filters.student_name || undefined,
    };
    const response = await apiClient.get('/enrollments/', { params });
    tableData.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("Failed to fetch enrollments:", error);
  } finally {
    loading.value = false;
  }
};

watch(() => props.visible, (newVal) => {
  if (newVal) {
    fetchData(1);
  }
});

const handlePageChange = (page: number) => {
  fetchData(page);
};

const handleSelectionChange = (val: any[]) => {
  multipleSelection.value = val;
};

const handleClose = () => {
  emit('update:visible', false);
};

const handleConfirm = () => {
  emit('confirm', multipleSelection.value);
  handleClose();
};
</script>

<style scoped>
.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>