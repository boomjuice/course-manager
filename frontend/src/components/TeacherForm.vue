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
      <el-form-item label="登录名" prop="username">
        <el-input v-model="formData.username" placeholder="用于登录的唯一用户名" :disabled="isEdit" />
      </el-form-item>
      <el-form-item label="密码" :prop="isEdit ? '' : 'password'">
        <el-input v-model="formData.password" type="password" show-password :placeholder="isEdit ? '留空则不修改密码' : '请输入初始密码'" />
      </el-form-item>
      <el-form-item label="联系方式" prop="contact_info">
        <el-input v-model="formData.contact_info" placeholder="请输入联系电话或邮箱" />
      </el-form-item>
      <el-form-item label="可教科目" prop="subject_ids">
        <el-select v-model="formData.subject_ids" multiple placeholder="请选择科目" style="width: 100%">
          <el-option v-for="item in subjectOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="可教年级" prop="grade_ids">
        <el-select v-model="formData.grade_ids" multiple placeholder="请选择年级" style="width: 100%">
          <el-option v-for="item in gradeOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态" prop="is_active">
        <el-switch v-model="formData.is_active" />
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
import { ref, watch, reactive, onMounted } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
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
  username: '',
  password: '',
  contact_info: '',
  subject_ids: [],
  grade_ids: [],
  is_active: true,
});

const formRules = reactive<FormRules>({
  username: [{ required: true, message: '登录名不能为空', trigger: 'blur' }],
  password: [{ required: true, message: '初始密码不能为空', trigger: 'blur' }],
  contact_info: [{ required: true, message: '联系方式不能为空', trigger: 'blur' }],
});

const subjectOptions = ref([]);
const gradeOptions = ref([]);

watch(() => props.teacherData, (newData) => {
  if (newData && newData.id) {
    isEdit.value = true;
    formData.id = newData.id;
    formData.username = newData.user_name;
    formData.password = ''; // 编辑时不显示密码
    formData.contact_info = newData.contact_info;
    formData.subject_ids = newData.subjects.map((s: any) => s.id);
    formData.grade_ids = newData.grades.map((g: any) => g.id);
    formData.is_active = newData.is_active;
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
        // 如果是编辑模式且密码为空，则不提交密码字段
        if (isEdit.value && !payload.password) {
          delete payload.password;
        }

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
    const [subjectRes, gradeRes] = await Promise.all([
      apiClient.get('/subjects/', { params: { page_size: 100 } }),
      apiClient.get('/grades/', { params: { page_size: 100 } })
    ]);
    subjectOptions.value = subjectRes.data.results;
    gradeOptions.value = gradeRes.data.results;
  } catch (error) {
    console.error('Failed to fetch options:', error);
  }
};

onMounted(() => {
  fetchOptions();
});
</script>
