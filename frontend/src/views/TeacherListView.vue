<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>教师列表</span>
        <el-button type="primary" @click="handleAdd">新增教师</el-button>
      </div>
    </template>

    <!-- 筛选/搜索区 -->
    <el-form :inline="true" :model="filters" @submit.prevent="fetchTeachers">
      <el-form-item label="教师姓名">
        <el-input v-model="filters.search" placeholder="按姓名或登录名搜索" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetchTeachers">查询</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
    <el-table :data="teacherData" v-loading="loading" style="width: 100%">
      <el-table-column prop="user_name" label="登录名" width="120" />
      <el-table-column prop="contact_info" label="联系方式" width="150" />
      <el-table-column label="可教科目" min-width="150">
        <template #default="scope">
          <el-tag v-for="s in scope.row.subjects" :key="s.id" class="table-tag">{{ s.name }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="可教年级" min-width="150">
        <template #default="scope">
          <el-tag v-for="g in scope.row.grades" :key="g.id" class="table-tag" type="success">{{ g.name }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="scope">
          <el-tag :type="scope.row.is_active ? 'success' : 'info'">
            {{ scope.row.is_active ? '在职' : '离职' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_by" label="创建人" width="120" />
      <el-table-column label="创建时间" width="180">
        <template #default="scope">{{ formatTime(scope.row.created_time) }}</template>
      </el-table-column>
      <el-table-column prop="updated_by" label="修改人" width="120" />
      <el-table-column label="修改时间" width="180">
        <template #default="scope">{{ formatTime(scope.row.updated_time) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="scope">
          <el-button link type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="handleDelete(scope.row)">删除</el-button>
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

  <!-- 新增/编辑教师的弹窗 -->
  <TeacherForm
    v-model:visible="dialogVisible"
    :teacher-data="selectedTeacher"
    @success="onFormSuccess"
  />

</template>

<script lang="ts" setup>
import { ref, onMounted, reactive } from 'vue';
import apiClient from '@/api';
import {formatTime} from "@/utils/format.ts";
import { ElMessage, ElMessageBox } from 'element-plus';
import TeacherForm from '@/components/TeacherForm.vue';

// --- state ---
const teacherData = ref([]);
const loading = ref(false);
const total = ref(0);
const pageSize = ref(20);
const currentPage = ref(1);

const filters = reactive({
  search: '',
});

const dialogVisible = ref(false);
const selectedTeacher = ref(null);

// --- methods ---
const fetchTeachers = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      search: filters.search || undefined,
    };
    const response = await apiClient.get('/teachers/', { params });
    teacherData.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("Failed to fetch teachers:", error);
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchTeachers();
};

const handleAdd = () => {
  selectedTeacher.value = null;
  dialogVisible.value = true;
};

const handleEdit = (row: any) => {
  selectedTeacher.value = row;
  dialogVisible.value = true;
};

const handleDelete = (row: any) => {
  ElMessageBox.confirm(
    `确定要删除教师 "${row.user_name}" 吗？此操作不可恢复。`,
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await apiClient.delete(`/teachers/${row.id}/`);
      ElMessage.success('教师删除成功');
      fetchTeachers();
    } catch (error) {
      console.error('Failed to delete teacher:', error);
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
};

const onFormSuccess = () => {
  ElMessage.success('操作成功');
  fetchTeachers();
};

// --- lifecycle ---
onMounted(() => {
  fetchTeachers();
});
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.table-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}
.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
