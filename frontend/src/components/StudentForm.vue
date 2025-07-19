<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑学生' : '新增学生'"
    width="500px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
    >
      <el-form-item label="学生姓名" prop="name">
        <el-input v-model="formData.name" placeholder="请输入学生姓名" />
      </el-form-item>
      <el-form-item label="家长联系方式" prop="parent_contact_info">
        <el-input v-model="formData.parent_contact_info" placeholder="请输入家长联系方式" />
      </el-form-item>
      <el-form-item label="标签" prop="tag_ids">
        <el-select
          v-model="formData.tag_ids"
          multiple
          filterable
          placeholder="请选择学生标签"
          style="width: 100%"
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
import { ref, watch, reactive, onMounted, computed } from 'vue';
import type { FormInstance, FormRules } from 'element-plus';
import apiClient from '@/api';

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
  parent_contact_info: '',
  tag_ids: [],
  is_active: true,
});

const formRules = reactive<FormRules>({
  name: [{ required: true, message: '学生姓名不能为空', trigger: 'blur' }],
});

const allTags = ref([]);
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

watch(() => props.studentData, (newData) => {
  if (newData && newData.id) {
    isEdit.value = true;
    formData.id = newData.id;
    formData.name = newData.name;
    formData.parent_contact_info = newData.parent_contact_info;
    formData.tag_ids = newData.tags.map((tag: any) => tag.id);
    formData.is_active = newData.is_active;
  } else {
    isEdit.value = false;
    formRef.value?.resetFields();
    formData.id = null;
    formData.tag_ids = [];
    formData.is_active = true;
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
        const payload = {
          name: formData.name,
          parent_contact_info: formData.parent_contact_info,
          tag_ids: formData.tag_ids,
          is_active: formData.is_active,
        };

        if (isEdit.value) {
          await apiClient.put(`/students/${formData.id}/`, payload);
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

const fetchTags = async () => {
  try {
    const response = await apiClient.get('/tags/', { params: { page_size: 100 } });
    allTags.value = response.data.results;
  } catch (error) {
    console.error('Failed to fetch tags:', error);
  }
};

onMounted(() => {
  fetchTags();
});
</script>