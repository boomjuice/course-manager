<template>
  <el-dialog
    :model-value="visible"
    title="新增课程安排"
    width="500px"
    @close="handleClose"
  >
    <div v-if="selectionInfo" class="selection-info">
      <p><strong>开始时间:</strong> {{ formatTime(selectionInfo.start) }}</p>
      <p><strong>结束时间:</strong> {{ formatTime(selectionInfo.end) }}</p>
    </div>
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="80px"
      style="margin-top: 20px;"
    >
      <el-form-item label="班级" prop="teaching_class">
        <el-select v-model="formData.teaching_class" filterable placeholder="请选择班级" style="width: 100%;">
          <el-option v-for="item in classOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="教室" prop="classroom">
        <el-select v-model="formData.classroom" filterable placeholder="请选择教室" style="width: 100%;">
          <el-option v-for="item in classroomOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">确定</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import apiClient from '@/api';
import { ElMessage } from 'element-plus';

const props = defineProps<{
  visible: boolean;
  selectionInfo: { start: Date, end: Date } | null;
}>();
const emit = defineEmits(['update:visible', 'success']);

const formRef = ref<FormInstance>();
const loading = ref(false);

const formData = reactive({
  teaching_class: null,
  classroom: null,
});

const formRules = reactive<FormRules>({
  teaching_class: [{ required: true, message: '必须选择一个班级', trigger: 'change' }],
  classroom: [{ required: true, message: '必须选择一个教室', trigger: 'change' }],
});

const classOptions = ref([]);
const classroomOptions = ref([]);

const handleClose = () => {
  emit('update:visible', false);
};

const handleSubmit = async () => {
  if (!formRef.value || !props.selectionInfo) return;
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const payload = {
          ...formData,
          start_time: props.selectionInfo.start.toISOString(),
          end_time: props.selectionInfo.end.toISOString(),
        };
        await apiClient.post('/schedule-entries/', payload);
        ElMessage.success('课程创建成功！');
        emit('success');
        handleClose();
      } catch (error) {
        console.error('Failed to create schedule entry:', error);
      } finally {
        loading.value = false;
      }
    }
  });
};

const fetchOptions = async () => {
  try {
    const [classRes, classroomRes] = await Promise.all([
      apiClient.get('/teaching-classes/', { params: { page_size: 200 } }),
      apiClient.get('/classrooms/', { params: { page_size: 200 } })
    ]);
    classOptions.value = classRes.data.results;
    classroomOptions.value = classroomRes.data.results;
  } catch (error) {
    console.error('Failed to fetch options:', error);
  }
};

const formatTime = (date: Date) => {
  if (!date) return '';
  return date.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  });
};

onMounted(() => {
  fetchOptions();
});
</script>

<style scoped>
.selection-info {
  background-color: #f4f4f5;
  padding: 8px 16px;
  border-radius: 4px;
}
.selection-info p {
  margin: 4px 0;
}
</style>
