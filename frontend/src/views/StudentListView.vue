<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>学生管理</span>
        <el-button type="primary" @click="handleAdd">新增学生</el-button>
      </div>
    </template>

    <!-- 筛选/搜索区 -->
    <el-form :inline="true" :model="filters" @submit.prevent="fetchStudents">
      <el-form-item label="年级">
        <el-select v-model="filters.grade" style="width: 150px" placeholder="按年级筛选" clearable>
          <el-option v-for="item in gradeOptions" :key="item.id" :label="item.item_value" :value="item.id"/>
        </el-select>
      </el-form-item>
      <el-form-item label="学生">
        <el-input v-model="filters.search" placeholder="按学生名称搜索" clearable/>
      </el-form-item>
      <el-form-item label="标签">
        <el-select v-model="filters.tags" multiple placeholder="按标签筛选" style="width: 240px;">
          <el-option-group
              v-for="group in groupedTagOptions"
              :key="group.label"
              :label="group.label"
          >
            <el-option
                v-for="item in group.options"
                :key="item.id"
                :label="item.item_value"
                :value="item.id"
            />
          </el-option-group>
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="fetchStudents">查询</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据表格 -->
    <el-table :data="studentData" v-loading="loading" style="width: 100%">
      <el-table-column prop="name" label="姓名"/>
      <el-table-column prop="school" label="学校"/>
      <el-table-column prop="grade.item_value" label="年级"/>
      <el-table-column prop="parent_contact_info" min-width="120px" label="家长联系方式"/>
      <el-table-column label="标签">
        <template #default="scope">
          <div class="tag-container">
            <el-tag
                v-for="tag in scope.row.tags"
                :key="tag.id"
                class="tag"
                :color="getTagColor(tag.subgroup)"
                style="color: white;"
            >
              {{ tag.subgroup ? `${tag.subgroup}: ${tag.item_value}` : tag.item_value }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="notes" label="备注" width="100">
        <template #default="scope">
          <el-tooltip
              v-if="scope.row.notes"
              effect="dark"
              :content="scope.row.notes"
              placement="top"
          >
            <div class="notes-cell">{{ scope.row.notes }}</div>
          </el-tooltip>
          <span v-else>-</span>
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

  <!-- 新增/编辑学生的弹窗 -->
  <StudentForm
      v-model:visible="studentFormVisible"
      :student-data="selectedStudent"
      @success="onFormSuccess"
  />
</template>

<script lang="ts" setup>
import {ref, onMounted, reactive, computed} from 'vue';
import apiClient from '@/api';
import {ElMessage, ElMessageBox} from 'element-plus';
import StudentForm from '@/components/StudentForm.vue';
import {getTagColor} from '@/utils/colors';
import {formatTime} from "@/utils/format.ts";

// --- state ---
const studentData = ref([]);
const loading = ref(false);
const total = ref(0);
const pageSize = ref(20);
const currentPage = ref(1);

const filters = reactive({
  search: '',
  grade: null,
  tags: [],
});

const tagOptions = ref([]);
const gradeOptions = ref([]);
const studentFormVisible = ref(false);
const selectedStudent = ref(null);

const groupedTagOptions = computed(() => {
  const grouped = {};
  tagOptions.value.forEach(tag => {
    const groupKey = tag.subgroup || '未分组';
    if (!grouped[groupKey]) {
      grouped[groupKey] = {label: groupKey, options: []};
    }
    grouped[groupKey].options.push(tag);
  });
  return Object.values(grouped);
});

// --- methods ---
const fetchStudents = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      search: filters.search || undefined,
      grade: filters.grade || undefined,
      tags: filters.tags.join(',') || undefined,
    };
    const response = await apiClient.get('/students/', {params});
    studentData.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    console.error("Failed to fetch students:", error);
  } finally {
    loading.value = false;
  }
};

const fetchFilterOptions = async () => {
  try {
    const [tagsRes, gradesRes] = await Promise.all([
      apiClient.get('/data-dictionary/', {params: {group_code: 'student_tags', page_size: 200}}),
      apiClient.get('/data-dictionary/', {params: {group_code: 'grades', page_size: 100}}),
    ]);
    tagOptions.value = tagsRes.data.results;
    gradeOptions.value = gradesRes.data.results;
  } catch (error) {
    console.error("Failed to fetch filter options:", error);
  }
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchStudents();
};

const handleAdd = () => {
  selectedStudent.value = null;
  studentFormVisible.value = true;
};

const handleEdit = (row: any) => {
  selectedStudent.value = row;
  studentFormVisible.value = true;
};

const handleDelete = (row: any) => {
  ElMessageBox.confirm(
      `确定要删除学生 "${row.name}" 吗？`,
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
  ).then(async () => {
    try {
      await apiClient.delete(`/students/${row.id}/`);
      ElMessage.success('学生删除成功');
      fetchStudents();
    } catch (error) {
      console.error('Failed to delete student:', error);
    }
  }).catch(() => {
    ElMessage.info('已取消删除');
  });
};

const onFormSuccess = () => {
  ElMessage.success('操作成功');
  fetchStudents();
};

// --- lifecycle ---
onMounted(() => {
  fetchStudents();
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

.tag-container {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.tag {
  margin: 0;
}

.notes-cell {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
