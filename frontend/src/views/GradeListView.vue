<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>年级列表</span>
        <el-button type="primary" @click="handleOpenDialog()">新增年级</el-button>
      </div>
    </template>

    <!-- 搜索区 -->
    <el-form :inline="true" :model="filters" @submit.prevent="fetchData">
      <el-form-item>
        <el-input v-model="filters.search" placeholder="按年级名称搜索" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetchData">查询</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
    <el-table :data="data" v-loading="loading" style="width: 100%">
      <el-table-column prop="name" label="年级名称" />
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

  <!-- 新增/编辑弹窗 -->
  <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑年级' : '新增年级'" width="400px">
    <el-form ref="formRef" :model="formData" :rules="formRules" label-width="80px">
      <el-form-item label="年级名称" prop="name">
        <el-input v-model="formData.name" placeholder="请输入年级名称" />
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
import {formatTime} from "@/utils/format.ts";
import { ElMessage, ElMessageBox } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';

// --- state ---
const data = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const formLoading = ref(false);
const isEdit = ref(false);
const formRef = ref<FormInstance>();
const formData = reactive({ id: null, name: '' });
const filters = reactive({ search: '' });
const formRules = reactive<FormRules>({
  name: [{ required: true, message: '名称不能为空', trigger: 'blur' }],
});

// --- methods ---
const fetchData = async () => {
  loading.value = true;
  try {
    const params = {
      search: filters.search || undefined,
      page_size: 100,
    };
    const response = await apiClient.get('/grades/', { params });
    data.value = response.data.results;
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
        if (isEdit.value) {
          await apiClient.put(`/grades/${formData.id}/`, { name: formData.name });
        } else {
          await apiClient.post('/grades/', { name: formData.name });
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
      await apiClient.delete(`/grades/${row.id}/`);
      ElMessage.success('删除成功');
      fetchData();
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  });
};

// --- lifecycle ---
onMounted(fetchData);
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
