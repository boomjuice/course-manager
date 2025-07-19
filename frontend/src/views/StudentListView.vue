<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>学生列表</span>
        <el-button type="primary" @click="handleAdd">新增学生</el-button>
      </div>
    </template>

    <!-- 筛选/搜索区 -->
    <el-form :inline="true" :model="filters" @submit.prevent="fetchStudents">
      <el-form-item label="学生姓名">
        <el-input v-model="filters.name" placeholder="按姓名搜索" clearable />
      </el-form-item>
      <el-form-item label="标签">
        <el-select
          v-model="filters.tags"
          multiple
          filterable
          placeholder="按标签筛选"
          style="width: 240px;"
        >
          <el-option-group
            v-for="group in groupedTagOptions"
            :key="group.label"
            :label="group.label"
          >
            <el-option
              v-for="item in group.options"
              :key="item.id"
              :label="item.name"
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
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="parent_contact_info" label="家长联系方式" width="150" />
      <el-table-column label="标签" min-width="180">
        <template #default="scope">
          <div v-for="(tags, group) in scope.row.grouped_tags" :key="group" class="tag-group">
            <el-tag
              v-for="tag in tags"
              :key="tag.id"
              :type="tagColorMap[tag.group]"
              class="table-tag"
              disable-transitions
            >
              {{ tag.group_display }}: {{ tag.name }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="scope">
          <el-tag :type="scope.row.is_active ? 'success' : 'info'">
            {{ scope.row.is_active ? '在读' : '禁用' }}
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

  <!-- 新增/编辑学生的弹窗 -->
  <StudentForm 
    v-model:visible="dialogVisible" 
    :student-data="selectedStudent"
    @success="onFormSuccess"
  />

</template>

<script lang="ts" setup>
import { ref, onMounted, reactive, computed } from 'vue';
import apiClient from '@/api';
import { ElMessage, ElMessageBox } from 'element-plus';
import StudentForm from '@/components/StudentForm.vue';
import { formatTime } from '@/utils/format'; // Import the utility function

// --- state ---
const studentData = ref([]);
const loading = ref(false);
const total = ref(0);
const pageSize = ref(20);
const currentPage = ref(1);

const filters = reactive({
  name: '',
  tags: [],
});

const dialogVisible = ref(false);
const selectedStudent = ref(null);
const allTags = ref([]);

const tagColorMap = {
  'performance': 'danger',
  'school_info': 'success',
  'personality': 'primary',
  'source': 'warning',
  'other': 'info',
};

const groupOptions = ref([
  { value: 'performance', label: '成绩表现' },
  { value: 'school_info', label: '学校信息' },
  { value: 'personality', label: '性格特点' },
  { value: 'source', label: '来源渠道' },
  { value: 'other', label: '其他' },
]);

const groupedTagOptions = computed(() => {
  const grouped = {};
  groupOptions.value.forEach(group => {
    grouped[group.value] = { label: group.label, options: [] };
  });

  allTags.value.forEach(tag => {
    if (grouped[tag.group]) {
      grouped[tag.group].options.push(tag);
    }
  });

  return Object.values(grouped).filter(g => g.options.length > 0);
});

// --- methods ---
const fetchStudents = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      search: filters.name || undefined,
      tags: filters.tags.length > 0 ? filters.tags.join(',') : undefined,
    };
    const response = await apiClient.get('/students/', { params });
    
    const processedResults = response.data.results.map(student => {
      const grouped_tags = {};
      student.tags.forEach(tag => {
        if (!grouped_tags[tag.group]) {
          grouped_tags[tag.group] = [];
        }
        grouped_tags[tag.group].push(tag);
      });
      return { ...student, grouped_tags };
    });

    studentData.value = processedResults;
    total.value = response.data.count;
  } catch (error) {
    console.error("Failed to fetch students:", error);
  } finally {
    loading.value = false;
  }
};

const fetchTagsForFilter = async () => {
  try {
    const response = await apiClient.get('/tags/', { params: { page_size: 200 } });
    allTags.value = response.data.results;
  } catch (error) {
    console.error("Failed to fetch tags for filter:", error);
  }
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchStudents();
};

const handleAdd = () => {
  selectedStudent.value = null;
  dialogVisible.value = true;
};

const handleEdit = (row: any) => {
  selectedStudent.value = row;
  dialogVisible.value = true;
};

const handleDelete = (row: any) => {
  ElMessageBox.confirm(
    `确定要删除学生 "${row.name}" 吗？此操作不可恢复。`,
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
  fetchTagsForFilter();
});
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tag-group {
  margin-bottom: 6px;
}
.table-tag {
  margin-right: 5px;
}
.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>