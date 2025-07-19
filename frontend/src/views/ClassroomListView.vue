<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>教室列表</span>
        <el-button type="primary" @click="handleOpenDialog()">新增教室</el-button>
      </div>
    </template>

    <!-- 搜索区 -->
    <el-form :inline="true" :model="filters" @submit.prevent="fetchData">
      <el-form-item>
        <el-input v-model="filters.search" placeholder="按教室名称搜索" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetchData">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="data" v-loading="loading" style="width: 100%">
      <el-table-column prop="name" label="教室名称" />
      <el-table-column prop="capacity" label="容量" />
      <el-table-column prop="campus_name" label="所属校区" />
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
          <el-button link type="primary" size="small" @click="handleOpenDialog(scope.row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑教室' : '新增教室'" width="500px">
    <el-form ref="formRef" :model="formData" :rules="formRules" label-width="80px">
      <el-form-item label="名称" prop="name">
        <el-input v-model="formData.name" />
      </el-form-item>
      <el-form-item label="容量" prop="capacity">
        <el-input-number v-model="formData.capacity" :min="1" />
      </el-form-item>
      <el-form-item label="校区" prop="campus">
        <el-select v-model="formData.campus" placeholder="请选择校区">
          <el-option v-for="c in campusOptions" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="formLoading">确定</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, onMounted, reactive } from 'vue';
import apiClient from '@/api';
import { formatTime } from '@/utils/format';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';

const data = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const formLoading = ref(false);
const isEdit = ref(false);
const formRef = ref<FormInstance>();
const formData = reactive({ id: null, name: '', capacity: 10, campus: null });
const filters = reactive({ search: '' });
const campusOptions = ref([]);

const formRules = reactive<FormRules>({
  name: [{ required: true, message: '名称不能为空', trigger: 'blur' }],
  capacity: [{ required: true, message: '容量不能为空', trigger: 'blur' }],
  campus: [{ required: true, message: '必须选择一个校区', trigger: 'change' }],
});

const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      search: filters.search || undefined,
      page_size: 100,
    };
    const [classroomsRes, campusesRes] = await Promise.all([
      apiClient.get('/classrooms/', { params }),
      apiClient.get('/campuses/', { params: { page_size: 100 } })
    ]);
    data.value = classroomsRes.data.results;
    campusOptions.value = campusesRes.data.results;
  } catch (error) {
    console.error("Failed to fetch data:", error);
  } finally {
    loading.value = false;
  }
};

const handleOpenDialog = (row?: any) => {
  isEdit.value = !!row;
  if (row) {
    formData.id = row.id;
    formData.name = row.name;
    formData.capacity = row.capacity;
    formData.campus = row.campus;
  } else {
    formRef.value?.resetFields();
    formData.id = null;
  }
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (valid) {
      formLoading.value = true;
      try {
        const payload = { ...formData };
        if (isEdit.value) {
          await apiClient.put(`/classrooms/${payload.id}/`, payload);
        } else {
          await apiClient.post('/classrooms/', payload);
        }
        ElMessage.success('操作成功');
        dialogVisible.value = false;
        fetchData();
      } catch (error) {
        console.error('Failed to save:', error);
      } finally {
        formLoading.value = false;
      }
    }
  });
};

const handleDelete = (row: any) => {
  ElMessageBox.confirm(`确定要删除 "${row.name}" 吗？`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await apiClient.delete(`/classrooms/${row.id}/`);
      ElMessage.success('删除成功');
      fetchData();
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  });
};

onMounted(fetchData);
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
