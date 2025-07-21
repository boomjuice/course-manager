<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>教师管理</span>
        <el-button type="primary" @click="handleAdd">新增教师</el-button>
      </div>
    </template>

    <!-- 筛选/搜索区 -->
    <el-form :inline="true" :model="filters" @submit.prevent="fetchData">
      <el-form-item label="科目">
        <el-select v-model="filters.subjects" style="width: 150px" placeholder="按科目筛选"
                   clearable>
          <el-option v-for="item in subjectOptions" :key="item.id" :label="item.item_value"
                     :value="item.id"/>
        </el-select>
      </el-form-item>
      <el-form-item label="年级">
        <el-select v-model="filters.grades" style="width: 150px" placeholder="按年级筛选" clearable>
          <el-option v-for="item in gradeOptions" :key="item.id" :label="item.item_value"
                     :value="item.id"/>
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetchData">查询</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
    <el-table :data="tableData" v-loading="loading" style="width: 100%">
      <el-table-column prop="name" label="姓名"/>
      <el-table-column prop="contact_info" label="联系方式"/>
      <el-table-column label="可教科目">
        <template #default="scope">
          <el-tag v-for="item in scope.row.subjects" :key="item.id" :label="item.value" class="tag">
            {{ item.item_value }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="可教年级">
        <template #default="scope">
          <el-tag v-for="item in scope.row.grades" :key="item.id" :label="item.value" class="tag"
                  type="success">{{ item.item_value }}
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
  <TeacherForm
    v-model:visible="formVisible"
    :teacher-data="selectedTeacher"
    @success="onFormSuccess"
  />
</template>

<script lang="ts" setup>
import {ref, onMounted, reactive} from 'vue';
import apiClient from '@/api';
import {ElMessage, ElMessageBox} from 'element-plus';
import TeacherForm from '@/components/TeacherForm.vue';
import {formatTime} from "@/utils/format.ts";

// --- state ---
const tableData = ref([]);
const loading = ref(false);
const total = ref(0);
const pageSize = ref(20);
const currentPage = ref(1);

const filters = reactive({
  subjects: null,
  grades: null,
});

const subjectOptions = ref([]);
const gradeOptions = ref([]);
const formVisible = ref(false);
const selectedTeacher = ref(null);

// --- methods ---
const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      subjects: filters.subjects || undefined,
      grades: filters.grades || undefined,
    };
    const response = await apiClient.get('/teachers/', {params});
    tableData.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("Failed to fetch teachers:", error);
  } finally {
    loading.value = false;
  }
};

const fetchFilterOptions = async () => {
  try {
    const [subjectsRes, gradesRes] = await Promise.all([
      apiClient.get('/data-dictionary/', {params: {group_code: 'subjects', page_size: 100}}),
      apiClient.get('/data-dictionary/', {params: {group_code: 'grades', page_size: 100}}),
    ]);
    subjectOptions.value = subjectsRes.data.results;
    gradeOptions.value = gradesRes.data.results;
  } catch (error) {
    console.error("Failed to fetch filter options:", error);
  }
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchData();
};

const handleAdd = () => {
  selectedTeacher.value = null;
  formVisible.value = true;
};

const handleEdit = (row: any) => {
  selectedTeacher.value = row;
  formVisible.value = true;
};

const handleDelete = (row: any) => {
  ElMessageBox.confirm(
    `确定要删除教师 "${row.name}" 吗？`,
    '警告',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await apiClient.delete(`/teachers/${row.id}/`);
      ElMessage.success('删除成功');
      fetchData();
    } catch (error) {
      console.error('Failed to delete teacher:', error);
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
};

const onFormSuccess = () => {
  ElMessage.success('操作成功');
  fetchData();
};

// --- lifecycle ---
onMounted(() => {
  fetchData();
  fetchFilterOptions();
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

.tag {
  margin-right: 5px;
}
</style>
