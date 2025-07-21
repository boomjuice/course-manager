<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>开班计划管理</span>
        <el-button type="primary" @click="handleAdd">新建开班计划</el-button>
      </div>
    </template>

    <!-- 筛选/搜索区 -->
    <el-form :inline="true" :model="filters" @submit.prevent="fetchData">
      <el-form-item label="计划名称">
        <el-input v-model="filters.name" placeholder="按名称搜索" clearable/>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="filters.status" style="width: 120px" placeholder="按状态筛选" clearable>
          <el-option label="计划中" value="planning"/>
          <el-option label="报名中" value="open"/>
          <el-option label="已开课" value="in_progress"/>
          <el-option label="已结束" value="completed"/>
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetchData">查询</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
    <el-table :data="tableData" v-loading="loading" style="width: 100%">
      <el-table-column prop="name" min-width="100px" label="计划名称"/>
      <el-table-column prop="course_product.display_name" min-width="100px" label="课程产品"/>
      <el-table-column label="报名情况">
        <template #default="scope">
          <el-button link type="primary" @click="showEnrolledStudents(scope.row)">
            {{ scope.row.enrollment_count }} 人
          </el-button>
        </template>
      </el-table-column>
      <el-table-column prop="start_date" label="开始日期"/>
      <el-table-column prop="end_date" label="结束日期"/>
      <el-table-column prop="status" label="状态">
        <template #default="scope">
          <el-tag :type="getStatusTagType(scope.row.status)">{{
              getStatusText(scope.row.status)
            }}
          </el-tag>
        </template>
      </el-table-column>
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
  <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑开班计划' : '新建开班计划'"
             width="500px">
    <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
      <el-form-item label="课程产品" prop="course_product_id">
        <el-select v-model="formData.course_product_id" filterable placeholder="请选择课程产品">
          <el-option v-for="item in courseProductOptions" :key="item.id" :label="item.display_name"
                     :value="item.id"/>
        </el-select>
      </el-form-item>
      <el-form-item label="计划名称" prop="name">
        <el-input v-model="formData.name"/>
      </el-form-item>
      <el-form-item label="日期范围" prop="date_range">
        <el-date-picker
          v-model="formData.date_range"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
        />
        <div class="el-form-item__help">
          此日期范围将用于限制后续的排课操作，请谨慎设置。
        </div>
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="formData.status" placeholder="请选择状态">
          <el-option label="计划中" value="planning"/>
          <el-option label="报名中" value="open"/>
          <el-option label="已开课" value="in_progress"/>
          <el-option label="已结束" value="completed"/>
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="formLoading">确定</el-button>
    </template>
  </el-dialog>

  <!-- 报名学生列表弹窗 -->
  <EnrolledStudentsDialog v-model:visible="studentsDialogVisible" :students="selectedStudents"/>
</template>

<script lang="ts" setup>
import {ref, onMounted, reactive} from 'vue';
import apiClient from '@/api';
import {ElMessage, ElMessageBox} from 'element-plus';
import type {FormInstance, FormRules} from 'element-plus';
import dayjs from 'dayjs';
import EnrolledStudentsDialog from '@/components/EnrolledStudentsDialog.vue';
import {formatTime} from "@/utils/format.ts";

// --- state ---
const tableData = ref([]);
const loading = ref(false);
const total = ref(0);
const pageSize = ref(20);
const currentPage = ref(1);

const filters = reactive({
  name: '',
  status: '',
});

const dialogVisible = ref(false);
const formLoading = ref(false);
const isEdit = ref(false);
const formRef = ref<FormInstance>();
const formData = reactive({
  id: null,
  name: '',
  course_product_id: null,
  date_range: [],
  status: 'planning',
});

const formRules = reactive<FormRules>({
  name: [{required: true, message: '计划名称不能为空', trigger: 'blur'}],
  course_product_id: [{required: true, message: '必须选择课程产品', trigger: 'change'}],
  date_range: [{required: true, message: '必须选择日期范围', trigger: 'change'}],
  status: [{required: true, message: '必须选择状态', trigger: 'change'}],
});

const courseProductOptions = ref([]);
const studentsDialogVisible = ref(false);
const selectedStudents = ref([]);

// --- methods ---
const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      search: filters.name || undefined,
      status: filters.status || undefined,
    };
    const response = await apiClient.get('/course-offerings/', {params});
    tableData.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("Failed to fetch course offerings:", error);
  } finally {
    loading.value = false;
  }
};

const fetchCourseProducts = async () => {
  try {
    const response = await apiClient.get('/course-products/', {params: {page_size: 1000}});
    courseProductOptions.value = response.data.results;
  } catch (error) {
    console.error("Failed to fetch course products:", error);
  }
};

const getStatusText = (status: string) => {
  const map = {planning: '计划中', open: '报名中', in_progress: '已开课', completed: '已结束'};
  return map[status] || '未知';
};

const getStatusTagType = (status: string) => {
  const map = {planning: 'info', open: 'success', in_progress: 'primary', completed: 'warning'};
  return map[status] || 'info';
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchData();
};

const handleAdd = () => {
  isEdit.value = false;
  Object.assign(formData, {
    id: null,
    name: '',
    course_product_id: null,
    date_range: [],
    status: 'planning'
  });
  dialogVisible.value = true;
};

const handleEdit = (row: any) => {
  isEdit.value = true;
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    course_product_id: row.course_product.id,
    date_range: [row.start_date, row.end_date],
    status: row.status,
  });
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (valid) {
      formLoading.value = true;
      try {
        const payload = {
          name: formData.name,
          course_product_id: formData.course_product_id,
          start_date: dayjs(formData.date_range[0]).format('YYYY-MM-DD'),
          end_date: dayjs(formData.date_range[1]).format('YYYY-MM-DD'),
          status: formData.status,
        };
        if (isEdit.value) {
          await apiClient.put(`/course-offerings/${formData.id}/`, payload);
        } else {
          await apiClient.post('/course-offerings/', payload);
        }
        ElMessage.success('操作成功');
        dialogVisible.value = false;
        fetchData();
      } catch (error) {
        console.error('Failed to save course offering:', error);
      } finally {
        formLoading.value = false;
      }
    }
  });
};

const handleDelete = (row: any) => {
  ElMessageBox.confirm(
    `确定要删除开班计划 "${row.name}" 吗？`,
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await apiClient.delete(`/course-offerings/${row.id}/`);
      ElMessage.success('删除成功');
      fetchData();
    } catch (error) {
      console.error('Failed to delete offering:', error);
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
};

const showEnrolledStudents = (row: any) => {
  selectedStudents.value = row.enrolled_students;
  studentsDialogVisible.value = true;
};

// --- lifecycle ---
onMounted(() => {
  fetchData();
  fetchCourseProducts();
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
.el-form-item__help {
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
  margin-top: 4px;
}
</style>