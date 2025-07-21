<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>报名管理</span>
        <el-button type="primary" @click="handleAdd">新建报名</el-button>
      </div>
    </template>

    <!-- 筛选/搜索区 -->
    <el-form :inline="true" :model="filters" @submit.prevent="fetchData">
      <el-form-item label="学生">
        <el-input v-model="filters.student_name" placeholder="按学生姓名搜索" clearable/>
      </el-form-item>
      <el-form-item label="开班计划">
        <el-input v-model="filters.course_offering_name" placeholder="按开班计划搜索" clearable/>
      </el-form-item>
      <el-form-item label="创建时间">
        <el-date-picker
            v-model="filters.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetchData">查询</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
    <el-table :data="tableData" v-loading="loading" style="width: 100%">
      <el-table-column label="开班计划" min-width="160">
        <template #default="scope">
          <el-button link type="primary" @click="showOfferingDetail(scope.row.course_offering)">
            {{ scope.row.course_offering.display_name }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="学生">
        <template #default="scope">
          <el-button link type="primary" @click="showStudentDetail(scope.row.student)">{{
              scope.row.student.name
            }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column prop="total_lessons" label="总课时"/>
      <el-table-column label="已消耗课时">
        <template #default="scope">
          <el-button link type="primary" @click="showConsumptionHistory(scope.row)">{{ scope.row.used_lessons }}</el-button>
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

  <!-- 新增/编辑弹窗 -->
  <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑报名' : '新建报名'" width="500px">
    <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
      <el-form-item label="学生" prop="student_id">
        <el-select v-model="formData.student_id" filterable placeholder="请选择学生">
          <el-option v-for="item in studentOptions" :key="item.id" :label="item.name" :value="item.id"/>
        </el-select>
      </el-form-item>
      <el-form-item label="开班计划" prop="course_offering_id">
        <el-select v-model="formData.course_offering_id" filterable placeholder="请选择开班计划">
          <el-option v-for="item in courseOfferingOptions" :key="item.id" :label="item.display_name" :value="item.id"/>
        </el-select>
        <div class="el-form-item__help">
          只显示“报名中”或“已开课”的计划。
        </div>
      </el-form-item>
      <el-form-item label="总课时" prop="total_lessons">
        <el-input-number v-model="formData.total_lessons" :min="0"/>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="formLoading">确定</el-button>
    </template>
  </el-dialog>

  <!-- 学生详情弹窗 -->
  <StudentDetailDialog v-model:visible="studentDetailVisible" :student="selectedStudent"/>
  <!-- 开班计划详情弹窗 -->
  <CourseOfferingDetailDialog v-model:visible="offeringDetailVisible" :offering="selectedOffering"/>
  <!-- 课时消耗历史弹窗 -->
  <ConsumptionHistoryDialog v-model:visible="historyDialogVisible" :enrollment-id="selectedEnrollmentId" />
</template>

<script lang="ts" setup>
import {ref, onMounted, reactive} from 'vue';
import apiClient from '@/api';
import {ElMessage, ElMessageBox} from 'element-plus';
import type {FormInstance, FormRules} from 'element-plus';
import StudentDetailDialog from '@/components/StudentDetailDialog.vue';
import CourseOfferingDetailDialog from '@/components/CourseOfferingDetailDialog.vue';
import ConsumptionHistoryDialog from '@/components/ConsumptionHistoryDialog.vue';
import dayjs from 'dayjs';
import {formatTime} from "@/utils/format.ts";

// --- state ---
const tableData = ref([]);
const loading = ref(false);
const total = ref(0);
const pageSize = ref(20);
const currentPage = ref(1);

const filters = reactive({
  student_name: '',
  course_offering_name: '',
  date_range: [],
});

const dialogVisible = ref(false);
const formLoading = ref(false);
const isEdit = ref(false);
const formRef = ref<FormInstance>();
const formData = reactive({
  id: null,
  student_id: null,
  course_offering_id: null,
  total_lessons: 0,
});

const formRules = reactive<FormRules>({
  student_id: [{required: true, message: '必须选择学生', trigger: 'change'}],
  course_offering_id: [{required: true, message: '必须选择开班计划', trigger: 'change'}],
  total_lessons: [{required: true, message: '总课时不能为空', trigger: 'blur'}],
});

const studentOptions = ref([]);
const courseOfferingOptions = ref([]);

const studentDetailVisible = ref(false);
const selectedStudent = ref(null);
const offeringDetailVisible = ref(false);
const selectedOffering = ref(null);
const historyDialogVisible = ref(false);
const selectedEnrollmentId = ref(null);

// --- methods ---
const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      student__name__icontains: filters.student_name || undefined,
      course_offering__name__icontains: filters.course_offering_name || undefined,
      created_time__date__gte: filters.date_range && filters.date_range[0] ? dayjs(filters.date_range[0]).format('YYYY-MM-DD') : undefined,
      created_time__date__lte: filters.date_range && filters.date_range[1] ? dayjs(filters.date_range[1]).format('YYYY-MM-DD') : undefined,
    };
    const response = await apiClient.get('/enrollments/', {params});
    tableData.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("Failed to fetch enrollments:", error);
  } finally {
    loading.value = false;
  }
};

const fetchOptions = async () => {
  try {
    const [studentsRes, offeringsRes] = await Promise.all([
      apiClient.get('/students/', {params: {page_size: 1000}}),
      apiClient.get('/course-offerings/', {params: {page_size: 1000, status__in: 'open,in_progress'}}),
    ]);
    studentOptions.value = studentsRes.data.results;
    courseOfferingOptions.value = offeringsRes.data.results;
  } catch (error) {
    console.error("Failed to fetch options:", error);
  }
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchData();
};

const handleAdd = () => {
  isEdit.value = false;
  Object.assign(formData, {id: null, student_id: null, course_offering_id: null, total_lessons: 0});
  dialogVisible.value = true;
};

const handleEdit = (row: any) => {
  isEdit.value = true;
  Object.assign(formData, {
    id: row.id,
    student_id: row.student.id,
    course_offering_id: row.course_offering.id,
    total_lessons: row.total_lessons,
  });
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (valid) {
      formLoading.value = true;
      try {
        if (isEdit.value) {
          await apiClient.put(`/enrollments/${formData.id}/`, formData);
        } else {
          await apiClient.post('/enrollments/', formData);
        }
        ElMessage.success('操作成功');
        dialogVisible.value = false;
        fetchData();
      } catch (error) {
        console.error('Failed to save enrollment:', error);
      } finally {
        formLoading.value = false;
      }
    }
  });
};

const handleDelete = (row: any) => {
  ElMessageBox.confirm(
      `确定要删除报名记录 "${row.display_name}" 吗？`,
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
  ).then(async () => {
    try {
      await apiClient.delete(`/enrollments/${row.id}/`);
      ElMessage.success('删除成功');
      fetchData();
    } catch (error) {
      console.error('Failed to delete enrollment:', error);
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
};

const showStudentDetail = (student: any) => {
  selectedStudent.value = student;
  studentDetailVisible.value = true;
};

const showOfferingDetail = (offering: any) => {
  selectedOffering.value = offering;
  offeringDetailVisible.value = true;
};

const showConsumptionHistory = (enrollment: any) => {
  selectedEnrollmentId.value = enrollment.id;
  historyDialogVisible.value = true;
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
