<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>班级列表</span>
        <el-button type="primary" @click="handleAdd">新增班级</el-button>
      </div>
    </template>

    <!-- 筛选/搜索区 -->
    <el-form :inline="true" :model="filters" @submit.prevent="fetchClasses">
      <el-form-item>
        <el-input v-model="filters.search" placeholder="按班级名称搜索" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetchClasses">查询</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
    <el-table :data="classData" v-loading="loading" style="width: 100%">
      <el-table-column prop="name" label="班级名称" />
      <el-table-column prop="class_type" label="类型">
        <template #default="scope">
          {{ classTypeMap[scope.row.class_type] || '未知' }}
        </template>
      </el-table-column>
      <el-table-column prop="teacher.user_name" label="授课教师">
        <template #default="scope">
          <el-button link type="primary" @click="showTeacherDetail(scope.row.teacher)">
            {{ scope.row.teacher.user_name }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column prop="subject.name" label="科目" />
      <el-table-column prop="grade.name" label="年级" />
      <el-table-column label="学生数">
        <template #default="scope">
          <el-button
            link
            type="primary"
            @click="showStudentList(scope.row.students)"
            :disabled="scope.row.students.length === 0"
          >
            {{ scope.row.students.length }}
          </el-button>
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
      <el-table-column label="操作" width="180">
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

  <!-- 新增/编辑班级的弹窗 -->
  <ClassForm
    v-model:visible="classFormVisible"
    :class-data="selectedClass"
    @success="onFormSuccess"
  />

  <!-- 查看班内学生的弹窗 -->
  <StudentListDialog
    v-model:visible="studentListVisible"
    :students="studentsInClass"
  />

  <!-- 查看教师详情的弹窗 -->
  <TeacherDetailDialog
    v-model:visible="teacherDetailVisible"
    :teacher="selectedTeacherForDetail"
  />
</template>

<script lang="ts" setup>
import { ref, onMounted, reactive } from 'vue';
import apiClient from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import ClassForm from '@/components/ClassForm.vue';
import StudentListDialog from '@/components/StudentListDialog.vue';
import TeacherDetailDialog from '@/components/TeacherDetailDialog.vue';
import {formatTime} from "@/utils/format.ts";

// --- state ---
const classData = ref([]);
const loading = ref(false);
const total = ref(0);
const pageSize = ref(20);
const currentPage = ref(1);

const filters = reactive({
  search: '',
});

const classFormVisible = ref(false);
const selectedClass = ref(null);

const studentListVisible = ref(false);
const studentsInClass = ref([]);

const teacherDetailVisible = ref(false);
const selectedTeacherForDetail = ref(null);

const classTypeMap = {
  'small_group': '小班',
  'one_on_one': '一对一'
};

// --- methods ---
const fetchClasses = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      search: filters.search || undefined,
    };
    const response = await apiClient.get('/teaching-classes/', { params });
    classData.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("Failed to fetch classes:", error);
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchClasses();
};

const handleAdd = () => {
  selectedClass.value = null;
  classFormVisible.value = true;
};

const handleEdit = (row: any) => {
  selectedClass.value = row;
  classFormVisible.value = true;
};

const handleDelete = (row: any) => {
  ElMessageBox.confirm(
    `确定要删除班级 "${row.name}" 吗？`,
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await apiClient.delete(`/teaching-classes/${row.id}/`);
      ElMessage.success('班级删除成功');
      fetchClasses();
    } catch (error) {
      console.error('Failed to delete class:', error);
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
};

const onFormSuccess = () => {
  ElMessage.success('操作成功');
  fetchClasses();
};

const showStudentList = (students: any[]) => {
  studentsInClass.value = students;
  studentListVisible.value = true;
};

const showTeacherDetail = (teacher: any) => {
  selectedTeacherForDetail.value = teacher;
  teacherDetailVisible.value = true;
};

// --- lifecycle ---
onMounted(() => {
  fetchClasses();
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
