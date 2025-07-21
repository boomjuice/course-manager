<template>
  <div>
    <el-dialog
      :model-value="visible"
      title="批量排课"
      width="700px"
      @close="handleClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="日期范围" prop="date_range">
          <el-date-picker
            v-model="formData.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            @change="onDateChange"
          />
        </el-form-item>
        <el-form-item label="开班计划" prop="course_offering_id">
          <el-select v-model="formData.course_offering_id" filterable :placeholder="offeringPlaceholder" @change="onOfferingChange" :disabled="!formData.date_range || formData.date_range.length === 0">
            <el-option v-for="item in availableOfferings" :key="item.id" :label="item.display_name" :value="item.id" />
          </el-select>
          <div class="el-form-item__help">
            只显示在您所选日期范围内、且状态为“报名中”或“已开课”的计划。
          </div>
        </el-form-item>
        <el-form-item label="报名记录" prop="enrollment_ids">
          <div class="enrollment-display-wrapper">
            <div class="selected-enrollments">
              <el-tag
                v-for="enrollment in selectedEnrollments"
                :key="enrollment.id"
                closable
                @close="removeEnrollment(enrollment)"
              >
                {{ enrollment.student.name }}
              </el-tag>
              <span v-if="selectedEnrollments.length === 0" class="placeholder">请选择报名记录</span>
            </div>
            <el-button @click="selectorVisible = true" :disabled="!formData.course_offering_id">选择</el-button>
          </div>
        </el-form-item>
        <el-form-item label="授课教师" prop="teacher_id">
          <el-select v-model="formData.teacher_id" filterable :placeholder="teacherPlaceholder" :disabled="!formData.course_offering_id">
            <el-option v-for="item in availableTeachers" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
          <div class="el-form-item__help">
            只显示所选开班计划对应课程的、有授课资格的教师。
          </div>
        </el-form-item>
        <el-form-item label="教室" prop="classroom">
          <el-select v-model="formData.classroom" filterable placeholder="请选择教室">
            <el-option v-for="item in classroomOptions" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="重复日期" prop="days_of_week">
          <el-checkbox-group v-model="formData.days_of_week">
            <el-checkbox :label="0">周一</el-checkbox>
            <el-checkbox :label="1">周二</el-checkbox>
            <el-checkbox :label="2">周三</el-checkbox>
            <el-checkbox :label="3">周四</el-checkbox>
            <el-checkbox :label="4">周五</el-checkbox>
            <el-checkbox :label="5">周六</el-checkbox>
            <el-checkbox :label="6">周日</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="时间范围" prop="time_range">
          <el-time-picker
            v-model="formData.time_range"
            is-range
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">确定</el-button>
      </template>
    </el-dialog>

    <EnrollmentSelectorDialog
      v-model:visible="selectorVisible"
      :selected-ids="formData.enrollment_ids"
      :course-offering-id="formData.course_offering_id"
      @confirm="handleEnrollmentConfirm"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, computed } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import apiClient from '@/api';
import { ElMessage } from 'element-plus';
import dayjs from 'dayjs';
import EnrollmentSelectorDialog from './EnrollmentSelectorDialog.vue';

const props = defineProps<{
  visible: boolean;
}>();

const emit = defineEmits(['update:visible', 'success']);

const formRef = ref<FormInstance>();
const loading = ref(false);
const selectorVisible = ref(false);

const formData = reactive({
  course_offering_id: null,
  enrollment_ids: [],
  teacher_id: null,
  classroom: null,
  days_of_week: [],
  time_range: [],
  date_range: [],
});

const formRules = reactive<FormRules>({
  course_offering_id: [{ required: true, message: '必须选择开班计划', trigger: 'change' }],
  enrollment_ids: [{ required: true, type: 'array', min: 1, message: '至少选择一个报名记录', trigger: 'change' }],
  teacher_id: [{ required: true, message: '必须选择授课教师', trigger: 'change' }],
  classroom: [{ required: true, message: '必须选择教室', trigger: 'change' }],
  days_of_week: [{ required: true, message: '至少选择一个重复日期', trigger: 'change' }],
  time_range: [{ required: true, message: '必须选择时间范围', trigger: 'change' }],
  date_range: [{ required: true, message: '必须选择日期范围', trigger: 'change' }],
});

const allOfferings = ref([]);
const allEnrollments = ref([]);
const allTeachers = ref([]);
const classroomOptions = ref([]);

const availableOfferings = computed(() => {
  if (!formData.date_range || formData.date_range.length === 0) return [];
  return allOfferings.value;
});

const offeringPlaceholder = computed(() => {
  if (!formData.date_range || formData.date_range.length === 0) return '请先选择日期范围以筛选';
  if (allOfferings.value.length === 0) return '该日期范围内无可用开班计划';
  return '请选择开班计划';
});

const teacherPlaceholder = computed(() => {
  if (!formData.course_offering_id) return '请先选择开班计划以筛选';
  if (availableTeachers.value.length === 0) return '该计划无匹配的授课教师';
  return '请选择授课教师';
});

const selectedEnrollments = computed(() => {
  return allEnrollments.value.filter(e => formData.enrollment_ids.includes(e.id));
});

const availableTeachers = computed(() => {
  if (!formData.course_offering_id) return [];
  const offering = allOfferings.value.find(o => o.id === formData.course_offering_id);
  if (!offering || !offering.course_product) return [];
  const product = offering.course_product;
  return allTeachers.value.filter(teacher =>
    teacher.subjects.some(s => s.item_value === product.subject) &&
    teacher.grades.some(g => g.item_value === product.grade)
  );
});

const onDateChange = () => {
  formData.course_offering_id = null;
  formData.enrollment_ids = [];
  formData.teacher_id = null;
  fetchAvailableOfferings();
};

const onOfferingChange = () => {
  formData.enrollment_ids = [];
  formData.teacher_id = null;
};

const handleEnrollmentConfirm = (selected: any[]) => {
  formData.enrollment_ids = selected.map(item => item.id);
};

const removeEnrollment = (enrollment: any) => {
  formData.enrollment_ids = formData.enrollment_ids.filter(id => id !== enrollment.id);
};

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
          enrollment_ids: formData.enrollment_ids,
          teacher_id: formData.teacher_id,
          classroom: formData.classroom,
          days_of_week: formData.days_of_week,
          start_date: dayjs(formData.date_range[0]).format('YYYY-MM-DD'),
          end_date: dayjs(formData.date_range[1]).format('YYYY-MM-DD'),
          start_time: dayjs(formData.time_range[0]).format('HH:mm:ss'),
          end_time: dayjs(formData.time_range[1]).format('HH:mm:ss'),
        };

        await apiClient.post('/schedule-entries/batch-create/', payload);
        ElMessage.success('批量排课成功');
        emit('success');
        handleClose();
      } catch (error) {
        console.error('Failed to batch create schedule entries:', error);
      } finally {
        loading.value = false;
      }
    }
  });
};

const fetchAvailableOfferings = async () => {
  if (!formData.date_range || formData.date_range.length === 0) {
    allOfferings.value = [];
    return;
  }
  try {
    const params = {
      page_size: 1000,
      status__in: 'open,in_progress',
      start_date__lte: dayjs(formData.date_range[0]).format('YYYY-MM-DD'),
      end_date__gte: dayjs(formData.date_range[1]).format('YYYY-MM-DD'),
    };
    const response = await apiClient.get('/course-offerings/', { params });
    allOfferings.value = response.data.results;
  } catch (error) {
    console.error('Failed to fetch available offerings:', error);
  }
};

const fetchInitialOptions = async () => {
  try {
    const [enrollmentsRes, teachersRes, classroomsRes] = await Promise.all([
      apiClient.get('/enrollments/', { params: { page_size: 1000 } }),
      apiClient.get('/teachers/', { params: { page_size: 200 } }),
      apiClient.get('/classrooms/', { params: { page_size: 100 } }),
    ]);
    allEnrollments.value = enrollmentsRes.data.results;
    allTeachers.value = teachersRes.data.results;
    classroomOptions.value = classroomsRes.data.results;
  } catch (error: any) {
    ElMessage.error('加载选项失败: ' + (error.response?.data?.detail || error.message));
  }
};

onMounted(() => {
  fetchInitialOptions();
});
</script>

<style scoped>
.enrollment-display-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
}
.selected-enrollments {
  flex-grow: 1;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 5px;
  min-height: 32px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.placeholder {
  color: #a8abb2;
  font-size: 14px;
}
.el-form-item__help {
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
  margin-top: 4px;
}
</style>
