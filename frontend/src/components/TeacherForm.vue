<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑教师' : '新增教师'"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
    >
      <el-form-item label="姓名" prop="name">
        <el-input v-model="formData.name" placeholder="请输入姓名" :disabled="isEdit"/>
      </el-form-item>
      <el-form-item label="联系方式" prop="contact_info">
        <el-input v-model="formData.contact_info" placeholder="请输入联系电话或邮箱"/>
      </el-form-item>
      <el-form-item label="可教科目" prop="subject_ids">
        <el-select v-model="formData.subject_ids" multiple placeholder="请选择科目"
                   style="width: 100%">
          <el-option v-for="item in subjectOptions" :key="item.id" :label="item.item_value"
                     :value="item.id"/>
        </el-select>
      </el-form-item>
      <el-form-item label="可教年级" prop="grade_ids">
        <el-select v-model="formData.grade_ids" multiple placeholder="请选择年级"
                   style="width: 100%">
          <el-option v-for="item in gradeOptions" :key="item.id" :label="item.item_value"
                     :value="item.id"/>
        </el-select>
      </el-form-item>
      <el-form-item label="状态" prop="is_active">
        <el-switch v-model="formData.is_active"/>
      </el-form-item>
    </el-form>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          确定
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import {ref, watch, reactive, onMounted} from 'vue';
import type {FormInstance, FormRules} from 'element-plus';
import apiClient from '@/api';

const props = defineProps<{
  visible: boolean;
  teacherData: any;
}>();

const emit = defineEmits(['update:visible', 'success']);

const formRef = ref<FormInstance>();
const loading = ref(false);
const isEdit = ref(false);

const formData = reactive({
  id: null,
  name: '',
  username: '',
  contact_info: '',
  subject_ids: [],
  grade_ids: [],
  is_active: true,
});

const formRules = reactive<FormRules>({
  name: [{required: true, message: '姓名不能为空', trigger: 'blur'}],
  contact_info: [
    {required: true, message: '联系方式不能为空', trigger: 'blur'},
    {pattern: /^1[3-9]\d{9}$/, message: '请输入有效的11位手机号码', trigger: 'blur'}
  ]
});
const subjectOptions = ref([]);
const gradeOptions = ref([]);

watch(() => props.teacherData, (newData) => {
  if (newData && newData.id) {
    isEdit.value = true;
    formData.id = newData.id;
    formData.name = newData.name;
    formData.contact_info = newData.contact_info;
    formData.is_active = newData.is_active;
    formData.subject_ids = newData.subjects.map((s: any) => s.id);
    formData.grade_ids = newData.grades.map((g: any) => g.id);
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
        const payload = {...formData};
        if (isEdit.value) {
          await apiClient.put(`/teachers/${payload.id}/`, payload);
        } else {
          await apiClient.post('/teachers/', payload);
        }
        emit('success');
        handleClose();
      } catch (error) {
        console.error('Failed to save teacher:', error);
      } finally {
        loading.value = false;
      }
    }
  });
};

const fetchOptions = async () => {
  try {
    const [subjectsRes, gradesRes] = await Promise.all([
      apiClient.get('/data-dictionary/', {params: {group_code: 'subjects', page_size: 100}}),
      apiClient.get('/data-dictionary/', {params: {group_code: 'grades', page_size: 100}}),
    ]);
    subjectOptions.value = subjectsRes.data.results;
    gradeOptions.value = gradesRes.data.results;
  } catch (error) {
    console.error('Failed to fetch options:', error);
  }
};

onMounted(() => {
  fetchOptions();
});
</script>

