<template>
  <el-dialog
    :model-value="visible"
    title="批量排课"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
    >
      <el-form-item label="选择班级" prop="teaching_class_id">
        <el-select v-model="formData.teaching_class_id" filterable placeholder="请选择班级" style="width: 100%;">
          <el-option v-for="item in classOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="选择教室" prop="classroom_id">
        <el-select v-model="formData.classroom_id" filterable placeholder="请选择教室" style="width: 100%;">
          <el-option v-for="item in classroomOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="时间模板" prop="timeslot_id">
        <el-select v-model="formData.timeslot_id" placeholder="请选择时间段模板" style="width: 100%;">
          <el-option v-for="item in timeslotOptions" :key="item.id" :label="`${item.template_name} (${item.start_time} - ${item.end_time})`" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="日期范围" prop="dateRange">
        <el-date-picker
          v-model="formData.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 100%;"
        />
      </el-form-item>
      <el-form-item label="重复星期" prop="days_of_week">
        <el-checkbox v-model="checkAll" :indeterminate="isIndeterminate" @change="handleCheckAllChange">
          全选
        </el-checkbox>
        <el-checkbox-group v-model="formData.days_of_week" @change="handleCheckedDaysChange">
          <el-checkbox :label="0">周一</el-checkbox>
          <el-checkbox :label="1">周二</el-checkbox>
          <el-checkbox :label="2">周三</el-checkbox>
          <el-checkbox :label="3">周四</el-checkbox>
          <el-checkbox :label="4">周五</el-checkbox>
          <el-checkbox :label="5">周六</el-checkbox>
          <el-checkbox :label="6">周日</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">确定</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, watch } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import apiClient from '@/api';
import { ElMessage } from 'element-plus';

const props = defineProps<{
  visible: boolean;
  initialData?: any;
}>();
const emit = defineEmits(['update:visible', 'success']);

const formRef = ref<FormInstance>();
const loading = ref(false);

const formData = reactive({
  teaching_class_id: null,
  classroom_id: null,
  timeslot_id: null,
  dateRange: [],
  days_of_week: [],
});

watch(() => props.initialData, (newData) => {
  if (newData) {
    formData.dateRange = newData.dateRange;
    formData.days_of_week = newData.days_of_week;
  }
});

const formRules = reactive<FormRules>({
  teaching_class_id: [{ required: true, message: '必须选择一个班级', trigger: 'change' }],
  classroom_id: [{ required: true, message: '必须选择一个教室', trigger: 'change' }],
  timeslot_id: [{ required: true, message: '必须选择一个时间模板', trigger: 'change' }],
  dateRange: [{ required: true, message: '必须选择日期范围', trigger: 'change' }],
  days_of_week: [{ required: true, type: 'array', min: 1, message: '至少选择一个重复星期', trigger: 'change' }],
});

const classOptions = ref([]);
const classroomOptions = ref([]);
const timeslotOptions = ref([]);

// --- Check All Logic ---
const checkAll = ref(false);
const isIndeterminate = ref(false);
const allWeekdays = [0, 1, 2, 3, 4, 5, 6];

const handleCheckAllChange = (val: boolean) => {
  formData.days_of_week = val ? allWeekdays : [];
  isIndeterminate.value = false;
};

const handleCheckedDaysChange = (value: number[]) => {
  const checkedCount = value.length;
  checkAll.value = checkedCount === allWeekdays.length;
  isIndeterminate.value = checkedCount > 0 && checkedCount < allWeekdays.length;
};

// --- Core Methods ---
const handleClose = () => {
  emit('update:visible', false);
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const payload = {
          ...formData,
          start_date: formData.dateRange[0],
          end_date: formData.dateRange[1],
        };
        delete payload.dateRange;

        const response = await apiClient.post('/schedule-entries/batch-create/', payload);
        ElMessage.success(`成功创建 ${response.data.created_count} 节课程！`);
        emit('success');
        handleClose();
      } catch (error) {
        console.error('Failed to batch create schedule:', error);
      } finally {
        loading.value = false;
      }
    }
  });
};

const fetchOptions = async () => {
  try {
    const [classRes, classroomRes, timeslotRes] = await Promise.all([
      apiClient.get('/teaching-classes/', { params: { page_size: 200 } }),
      apiClient.get('/classrooms/', { params: { page_size: 200 } }),
      apiClient.get('/timeslots/', { params: { page_size: 200 } })
    ]);
    classOptions.value = classRes.data.results;
    classroomOptions.value = classroomRes.data.results;
    timeslotOptions.value = timeslotRes.data.results;
  } catch (error) {
    console.error('Failed to fetch options:', error);
  }
};

onMounted(() => {
  fetchOptions();
});
</script>
