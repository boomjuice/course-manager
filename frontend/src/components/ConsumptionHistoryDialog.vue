<template>
  <el-dialog
    :model-value="visible"
    title="课时消耗历史"
    width="700px"
    @close="handleClose"
  >
    <div v-if="loading">加载中...</div>
    <div v-else>
      <el-table :data="tableData" style="width: 100%">
        <el-table-column label="消耗时间">
          <template #default="scope">{{ formatTime( scope.row.date)}}</template>
        </el-table-column>
        <el-table-column prop="course_name" label="课程名称"/>
        <el-table-column prop="teacher_name" label="授课教师"/>
        <el-table-column prop="lessons_consumed" label="消耗课时"/>
      </el-table>
      <el-pagination
        v-if="total > 0"
        class="pagination"
        background
        layout="prev, pager, next, total"
        :total="total"
        :page-size="pageSize"
        @current-change="handlePageChange"
      />
    </div>
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import {ref, watch} from 'vue';
import apiClient from '@/api';
import {formatTime} from "@/utils/format.ts";

const props = defineProps<{
  visible: boolean;
  enrollmentId: number | null;
}>();

const emit = defineEmits(['update:visible']);

const loading = ref(false);
const tableData = ref([]);
const total = ref(0);
const pageSize = ref(10); // Should match backend pagination size
const currentPage = ref(1);

watch(() => props.enrollmentId, (newId) => {
  if (newId) {
    fetchData(1);
  }
});

const fetchData = async (page: number) => {
  if (!props.enrollmentId) return;
  loading.value = true;
  currentPage.value = page;
  try {
    const params = {page};
    const response = await apiClient.get(`/enrollments/${props.enrollmentId}/consumption-history/`, {params});
    tableData.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("Failed to fetch consumption history:", error);
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page: number) => {
  fetchData(page);
};

const handleClose = () => {
  emit('update:visible', false);
};
</script>

<style scoped>
.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
