<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>标签列表</span>
        <el-button type="primary" @click="handleOpenDialog()">新增标签</el-button>
      </div>
    </template>

    <!-- 筛选区 -->
    <el-form :inline="true" :model="filters" @submit.prevent="fetchData">
      <el-form-item label="按组别筛选">
        <el-select v-model="filters.group" placeholder="选择组别" clearable @change="fetchData">
          <el-option v-for="item in groupOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-input v-model="filters.search" placeholder="按标签名称搜索" clearable />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetchData">查询</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
    <el-table
      :data="tableData"
      v-loading="loading"
      style="width: 100%"
      row-key="id"
      border
      default-expand-all
    >
      <el-table-column prop="name" label="组别 / 名称" />
        <el-table-column prop="created_by" label="创建人" width="120" />
      <el-table-column label="创建时间" width="180">
        <template #default="scope">{{ formatTime(scope.row.created_time) }}</template>
      </el-table-column>
      <el-table-column prop="updated_by" label="修改人" width="120" />
      <el-table-column label="修改时间" width="180">
        <template #default="scope">{{ formatTime(scope.row.updated_time) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" align="center">

        <template #default="scope">
          <!-- 只在子节点（即真实标签）上显示操作按钮 -->
          <div v-if="!scope.row.isGroup">
            <el-button link type="primary" size="small" @click="handleOpenDialog(scope.row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(scope.row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </el-card>

  <!-- 新增/编辑弹窗 -->
  <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑标签' : '新增标签'" width="400px">
    <el-form ref="formRef" :model="formData" :rules="formRules" label-width="80px">
      <el-form-item label="标签组别" prop="group">
        <el-select v-model="formData.group" placeholder="请选择组别">
          <el-option v-for="item in groupOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="标签名称" prop="name">
        <el-input v-model="formData.name" placeholder="请输入标签名称" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="formLoading">确定</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, onMounted, reactive, computed } from 'vue';
import apiClient from '@/api';
import { formatTime } from '@/utils/format';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';

// --- state ---
const allTags = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const formLoading = ref(false);
const isEdit = ref(false);
const formRef = ref<FormInstance>();
const formData = reactive({ id: null, name: '', group: 'other' });
const filters = reactive({ search: '', group: '' });

const groupOptions = ref([
  { value: 'performance', label: '成绩表现' },
  { value: 'school_info', label: '学校信息' },
  { value: 'personality', label: '性格特点' },
  { value: 'source', label: '来源渠道' },
  { value: 'other', label: '其他' },
]);

const formRules = reactive<FormRules>({
  name: [{ required: true, message: '名称不能为空', trigger: 'blur' }],
  group: [{ required: true, message: '必须选择一个组别', trigger: 'change' }],
});

// --- computed ---
const tableData = computed(() => {
  const grouped = {};

  // 1. Filter tags based on search and group filters
  const filteredTags = allTags.value.filter(tag => {
    const searchMatch = !filters.search || tag.name.includes(filters.search);
    const groupMatch = !filters.group || tag.group === filters.group;
    return searchMatch && groupMatch;
  });

  // 2. Group the filtered tags
  filteredTags.forEach(tag => {
    if (!grouped[tag.group]) {
      const groupName = groupOptions.value.find(g => g.value === tag.group)?.label || tag.group;
      grouped[tag.group] = {
        id: tag.group, // Unique key for the group row
        name: groupName,
        isGroup: true,
        children: []
      };
    }
    grouped[tag.group].children.push({ ...tag, isGroup: false });
  });

  return Object.values(grouped);
});


// --- methods ---
const fetchData = async () => {
  loading.value = true;
  try {
    const response = await apiClient.get('/tags/', { params: { page_size: 200 } }); // Fetch all tags
    allTags.value = response.data.results;
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
    formData.group = row.group;
  } else {
    formRef.value?.resetFields();
    formData.id = null;
    formData.group = 'other';
  }
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (valid) {
      formLoading.value = true;
      try {
        const payload = { name: formData.name, group: formData.group };
        if (isEdit.value) {
          await apiClient.put(`/tags/${formData.id}/`, payload);
        } else {
          await apiClient.post('/tags/', payload);
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
  ElMessageBox.confirm(`确定要删除标签 "${row.name}" 吗？`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await apiClient.delete(`/tags/${row.id}/`);
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
