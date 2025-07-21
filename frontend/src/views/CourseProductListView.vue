<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>课程产品管理</span>
        <el-button type="primary" @click="handleAdd">新建产品</el-button>
      </div>
    </template>

    <!-- 筛选/搜索区 -->
    <el-form :inline="true" :model="filters" @submit.prevent="fetchData">
      <el-form-item label="科目">
        <el-select v-model="filters.subject" style="width: 150px" placeholder="按科目筛选"
                   clearable>
          <el-option v-for="item in subjectOptions" :key="item.id" :label="item.item_value"
                     :value="item.item_value"/>
        </el-select>
      </el-form-item>
      <el-form-item label="年级">
        <el-select v-model="filters.grade" style="width: 150px" placeholder="按年级筛选" clearable>
          <el-option v-for="item in gradeOptions" :key="item.id" :label="item.item_value"
                     :value="item.item_value"/>
        </el-select>
      </el-form-item>
      <el-form-item label="课程类型">
        <el-select v-model="filters.course_type" style="width: 150px" placeholder="按类型筛选"
                   clearable>
          <el-option v-for="item in courseTypeOptions" :key="item.id" :label="item.item_value"
                     :value="item.item_value"/>
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetchData">查询</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
    <el-table :data="tableData" v-loading="loading" style="width: 100%">
      <el-table-column prop="display_name" label="展示名称"/>
      <el-table-column prop="grade" label="年级"/>
      <el-table-column prop="subject" label="科目"/>
      <el-table-column prop="course_type" label="课程类型"/>
      <el-table-column prop="duration_minutes" label="标准课长(分钟)"/>
      <el-table-column prop="created_by" label="创建人" width="120"/>
      <el-table-column label="创建时间" width="180">
        <template #default="scope">{{ formatTime(scope.row.created_time) }}</template>
      </el-table-column>
      <el-table-column prop="updated_by" label="修改人" width="120"/>
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
  <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑产品' : '新建产品'" width="500px">
    <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
      <el-form-item label="年级" prop="grade">
        <el-select v-model="formData.grade" placeholder="请选择年级">
          <el-option v-for="item in gradeOptions" :key="item.id" :label="item.item_value"
                     :value="item.item_value"/>
        </el-select>
      </el-form-item>
      <el-form-item label="科目" prop="subject">
        <el-select v-model="formData.subject" placeholder="请选择科目">
          <el-option v-for="item in subjectOptions" :key="item.id" :label="item.item_value"
                     :value="item.item_value"/>
        </el-select>
      </el-form-item>
      <el-form-item label="课程类型" prop="course_type">
        <el-select v-model="formData.course_type" placeholder="请选择课程类型">
          <el-option v-for="item in courseTypeOptions" :key="item.id" :label="item.item_value"
                     :value="item.item_value"/>
        </el-select>
      </el-form-item>
      <el-form-item label="标准课长(分钟)" prop="duration_minutes">
        <el-input-number v-model="formData.duration_minutes" :min="1"/>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="formLoading">确定</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import {ref, onMounted, reactive} from 'vue';
import apiClient from '@/api';
import {ElMessage, ElMessageBox} from 'element-plus';
import type {FormInstance, FormRules} from 'element-plus';
import {formatTime} from "@/utils/format.ts";

// --- state ---
const tableData = ref([]);
const loading = ref(false);
const total = ref(0);
const pageSize = ref(20);
const currentPage = ref(1);

const filters = reactive({
  subject: '',
  grade: '',
  course_type: '',
});

const dialogVisible = ref(false);
const formLoading = ref(false);
const isEdit = ref(false);
const formRef = ref<FormInstance>();
const formData = reactive({
  id: null,
  subject: '',
  grade: '',
  course_type: '',
  duration_minutes: 60,
});

const formRules = reactive<FormRules>({
  subject: [{required: true, message: '必须选择科目', trigger: 'change'}],
  grade: [{required: true, message: '必须选择年级', trigger: 'change'}],
  course_type: [{required: true, message: '必须选择课程类型', trigger: 'change'}],
  duration_minutes: [{required: true, message: '标准课长不能为空', trigger: 'blur'}],
});

const subjectOptions = ref([]);
const gradeOptions = ref([]);
const courseTypeOptions = ref([]);

// --- methods ---
const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      subject: filters.subject || undefined,
      grade: filters.grade || undefined,
      course_type: filters.course_type || undefined,
    };
    const response = await apiClient.get('/course-products/', {params});
    tableData.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("Failed to fetch course products:", error);
  } finally {
    loading.value = false;
  }
};

const fetchOptions = async () => {
  try {
    const [subjectsRes, gradesRes, courseTypesRes] = await Promise.all([
      apiClient.get('/data-dictionary/', {params: {group_code: 'subjects', page_size: 100}}),
      apiClient.get('/data-dictionary/', {params: {group_code: 'grades', page_size: 100}}),
      apiClient.get('/data-dictionary/', {params: {group_code: 'course_types', page_size: 100}}),
    ]);
    subjectOptions.value = subjectsRes.data.results;
    gradeOptions.value = gradesRes.data.results;
    courseTypeOptions.value = courseTypesRes.data.results;
  } catch (error) {
    console.error("Failed to fetch dictionary options:", error);
  }
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchData();
};

const handleAdd = () => {
  isEdit.value = false;
  Object.assign(formData, {
    id: null,
    subject: '',
    grade: '',
    course_type: '',
    duration_minutes: 60
  });
  dialogVisible.value = true;
};

const handleEdit = (row: any) => {
  isEdit.value = true;
  Object.assign(formData, row);
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (valid) {
      formLoading.value = true;
      try {
        if (isEdit.value) {
          await apiClient.put(`/course-products/${formData.id}/`, formData);
        } else {
          await apiClient.post('/course-products/', formData);
        }
        ElMessage.success('操作成功');
        dialogVisible.value = false;
        fetchData();
      } catch (error) {
        console.error('Failed to save course product:', error);
      } finally {
        formLoading.value = false;
      }
    }
  });
};

const handleDelete = (row: any) => {
  ElMessageBox.confirm(
    `确定要删除产品 "${row.display_name}" 吗？`,
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await apiClient.delete(`/course-products/${row.id}/`);
      ElMessage.success('删除成功');
      fetchData();
    } catch (error) {
      console.error('Failed to delete product:', error);
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
};

// --- lifecycle ---
onMounted(() => {
  fetchData();
  fetchOptions();
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
