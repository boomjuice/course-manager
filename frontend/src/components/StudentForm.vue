<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑学生' : '新增学生'"
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
        <el-input v-model="formData.name" />
      </el-form-item>
      <el-form-item label="学校" prop="school">
        <el-input v-model="formData.school" />
      </el-form-item>
      <el-form-item label="年级" prop="grade_id">
        <el-select v-model="formData.grade_id"  placeholder="请选择年级" clearable>
          <el-option v-for="item in gradeOptions" :key="item.id" :label="item.item_value" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="家长联系方式"  prop="parent_contact_info">
        <el-input v-model="formData.parent_contact_info" />
      </el-form-item>
      <el-form-item label="标签" prop="tag_ids">
        <el-select v-model="formData.tag_ids" multiple placeholder="请选择标签" style="width: 100%;">
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
            >
              <span>{{ item.subgroup ? `${item.subgroup}: ${item.item_value}` : item.item_value }}</span>
            </el-option>
          </el-option-group>
        </el-select>
      </el-form-item>
      <el-form-item label="备注" prop="notes">
        <el-input v-model="formData.notes" type="textarea" />
      </el-form-item>
      <el-form-item label="状态" prop="is_active">
        <el-switch v-model="formData.is_active" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">确定</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { ref, watch, reactive, onMounted, computed } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import apiClient from '@/api';
import { ElMessage } from 'element-plus';

const props = defineProps<{
  visible: boolean;
  studentData: any;
}>();

const emit = defineEmits(['update:visible', 'success']);

const formRef = ref<FormInstance>();
const loading = ref(false);
const isEdit = ref(false);

const formData = reactive({
  id: null,
  name: '',
  school: '',
  grade_id: null,
  parent_contact_info: '',
  tag_ids: [],
  notes: '',
  is_active: true,
});

const formRules = reactive<FormRules>({
  name: [{ required: true, message: '学生姓名不能为空', trigger: 'blur' }],
  parent_contact_info: [
    { required: true, message: '家长联系方式不能为空', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的11位手机号码', trigger: 'blur' }
  ],
});

const tagOptions = ref([]);
const gradeOptions = ref([]);

const groupedTagOptions = computed(() => {
  const grouped = {};
  tagOptions.value.forEach(tag => {
    const groupKey = tag.subgroup || '未分组';
    if (!grouped[groupKey]) {
      grouped[groupKey] = { label: groupKey, options: [] };
    }
    grouped[groupKey].options.push(tag);
  });
  return Object.values(grouped);
});

watch(() => props.studentData, (newData) => {
  if (newData && newData.id) {
    isEdit.value = true;
    formData.id = newData.id;
    formData.name = newData.name;
    formData.school = newData.school;
    formData.grade_id = newData.grade?.id;
    formData.parent_contact_info = newData.parent_contact_info;
    formData.tag_ids = newData.tags.map((t: any) => t.id);
    formData.notes = newData.notes;
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
        if (isEdit.value) {
          await apiClient.put(`/students/${payload.id}/`, payload);
        } else {
          await apiClient.post('/students/', payload);
        }
        emit('success');
        handleClose();
      } catch (error) {
        console.error('Failed to save student:', error);
      } finally {
        loading.value = false;
      }
    }
  });
};

const fetchOptions = async () => {
  try {
    const [tagsRes, gradesRes] = await Promise.all([
      apiClient.get('/data-dictionary/', { params: { group_code: 'student_tags', page_size: 200 } }),
      apiClient.get('/data-dictionary/', { params: { group_code: 'grades', page_size: 100 } }),
    ]);
    tagOptions.value = tagsRes.data.results;
    gradeOptions.value = gradesRes.data.results;
  } catch (error) {
    console.error('Failed to fetch options:', error);
  }
};

onMounted(() => {
  fetchOptions();
});
</script>
