<template>
  <div>
    <el-dialog
      :model-value="visible"
      :title="isEdit ? '编辑学习小组' : '新建学习小组'"
      width="600px"
      @close="handleClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="小组名称" prop="name">
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="报名记录" prop="enrollment_ids">
          <div class="enrollment-select-wrapper">
            <el-select 
              v-model="formData.enrollment_ids" 
              multiple 
              filterable 
              style="width: 100%" 
              placeholder="请选择报名记录"
            >
              <el-option 
                v-for="item in enrollmentOptions" 
                :key="item.id" 
                :label="item.display_name" 
                :value="item.id" 
              />
            </el-select>
            <el-tooltip
              content="根据当前已选的第一个报名记录，推荐相同课程产品的其他报名"
              placement="top"
            >
              <el-button 
                @click="openRecommendDialog" 
                class="recommend-btn"
                :disabled="formData.enrollment_ids.length === 0"
              >
                智能推荐
              </el-button>
            </el-tooltip>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 推荐报名记录弹窗 -->
    <el-dialog v-model="recommendVisible" title="智能推荐报名记录" width="700px">
      <el-table :data="recommendedEnrollments" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column property="enrollment_name" label="报名名称" />
        <el-table-column property="student.name" label="学生" />
        <el-table-column property="course_product.name" label="课程产品" />
      </el-table>
      <template #footer>
        <el-button @click="recommendVisible = false">取消</el-button>
        <el-button type="primary" @click="addRecommendedEnrollments">添加到小组</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch, reactive, onMounted } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import apiClient from '@/api';
import { ElMessage } from 'element-plus';

const props = defineProps<{
  visible: boolean;
  studyGroupData: any;
}>();

const emit = defineEmits(['update:visible', 'success']);

const formRef = ref<FormInstance>();
const loading = ref(false);
const isEdit = ref(false);
const recommendVisible = ref(false);
const recommendedEnrollments = ref([]);
const selectedRecommended = ref([]);

const formData = reactive({
  id: null,
  name: '',
  enrollment_ids: [],
});

const formRules = reactive<FormRules>({
  name: [{ required: true, message: '小组名称不能为空', trigger: 'blur' }],
});

const enrollmentOptions = ref([]);

watch(() => props.studyGroupData, (newData) => {
  if (newData && newData.id) {
    isEdit.value = true;
    formData.id = newData.id;
    formData.name = newData.name;
    formData.enrollment_ids = newData.enrollments.map((e: any) => e.id);
  } else {
    isEdit.value = false;
    formRef.value?.resetFields();
    formData.id = null;
  }
});

const handleClose = () => {
  emit('update:visible', false);
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const payload = { ...formData };
        if (isEdit.value) {
          await apiClient.put(`/study-groups/${payload.id}/`, payload);
        } else {
          await apiClient.post('/study-groups/', payload);
        }
        emit('success');
        handleClose();
      } catch (error) {
        console.error('Failed to save study group:', error);
      } finally {
        loading.value = false;
      }
    }
  });
};

const openRecommendDialog = async () => {
  if (formData.enrollment_ids.length === 0) return;
  try {
    const baseEnrollmentId = formData.enrollment_ids[0];
    const response = await apiClient.get('/enrollments/recommendations/', {
      params: { enrollment_id: baseEnrollmentId }
    });
    recommendedEnrollments.value = response.data.filter(
      (rec: any) => !formData.enrollment_ids.includes(rec.id)
    );
    if (recommendedEnrollments.value.length === 0) {
      ElMessage.info('暂无更多可推荐的报名记录');
      return;
    }
    recommendVisible.value = true;
  } catch (error) {
    console.error("Failed to fetch recommendations:", error);
  }
};

const handleSelectionChange = (val: any[]) => {
  selectedRecommended.value = val;
};

const addRecommendedEnrollments = () => {
  const newIds = selectedRecommended.value.map((e: any) => e.id);
  const currentIds = new Set(formData.enrollment_ids);
  newIds.forEach(id => currentIds.add(id));
  formData.enrollment_ids = Array.from(currentIds);
  recommendVisible.value = false;
};

const fetchOptions = async () => {
  try {
    const response = await apiClient.get('/enrollments/', { params: { page_size: 200 } });
    enrollmentOptions.value = response.data.results;
  } catch (error) {
    console.error('Failed to fetch enrollments:', error);
  }
};

onMounted(() => {
  fetchOptions();
});
</script>

<style scoped>
.enrollment-select-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
}
.recommend-btn {
  margin-left: 8px;
}
</style>
