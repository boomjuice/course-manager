<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑条目' : '新建条目'"
    width="500px"
    @close="handleClose"
  >
    <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
      <el-form-item label="分组代码" prop="group_code">
        <el-radio-group v-model="selectedGroup" @change="onGroupChange">
          <el-radio v-for="group in groupCodeOptions" :key="group" :label="group">{{
              group
            }}
          </el-radio>
          <el-radio label="custom">自定义</el-radio>
        </el-radio-group>
        <el-input
          v-if="selectedGroup === 'custom'"
          v-model="customGroupCode"
          placeholder="请输入新的分组代码"
          class="mt-2"
        />
      </el-form-item>
      <el-form-item label="子分组" prop="subgroup">
        <el-input v-model="formData.subgroup"/>
      </el-form-item>
      <el-form-item label="显示值" prop="item_value">
        <el-input v-model="formData.item_value"/>
      </el-form-item>
      <el-form-item label="排序" prop="sort_order">
        <el-input-number v-model="formData.sort_order" :min="0"/>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">确定</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import {ref, watch, reactive} from 'vue';
import type {FormInstance, FormRules} from 'element-plus';
import apiClient from '@/api';
import {ElMessage} from 'element-plus';

const props = defineProps<{
  visible: boolean;
  itemData: any;
  groupCodeOptions: string[];
}>();

const emit = defineEmits(['update:visible', 'success']);

const formRef = ref<FormInstance>();
const loading = ref(false);
const isEdit = ref(false);
const selectedGroup = ref('');
const customGroupCode = ref('');

const formData = reactive({
  id: null,
  group_code: '',
  item_value: '',
  subgroup: '',
  sort_order: 0,
});

const formRules = reactive<FormRules>({
  group_code: [{required: true, message: '分组代码不能为空', trigger: 'blur'}],
  item_value: [{required: true, message: '显示值不能为空', trigger: 'blur'}],
});

watch(() => props.itemData, (newData) => {
  if (newData && newData.id) {
    isEdit.value = true;
    Object.assign(formData, newData);
    if (props.groupCodeOptions.includes(newData.group_code)) {
      selectedGroup.value = newData.group_code;
    } else {
      selectedGroup.value = 'custom';
      customGroupCode.value = newData.group_code;
    }
  } else {
    isEdit.value = false;
    formRef.value?.resetFields();
    Object.assign(formData, {
      id: null,
      group_code: '',
      item_value: '',
      subgroup: '',
      sort_order: 0
    });
    selectedGroup.value = '';
    customGroupCode.value = '';
  }
});

const onGroupChange = (value: string) => {
  if (value !== 'custom') {
    formData.group_code = value;
    customGroupCode.value = '';
  } else {
    formData.group_code = '';
  }
};

watch(customGroupCode, (newVal) => {
  if (selectedGroup.value === 'custom') {
    formData.group_code = newVal;
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
        let response;
        if (isEdit.value) {
          response = await apiClient.put(`/data-dictionary/${formData.id}/`, formData);
        } else {
          response = await apiClient.post('/data-dictionary/', formData);
        }
        emit('success', response.data);
        handleClose();
      } catch (error) {
        console.error('Failed to save data dictionary item:', error);
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>

<style scoped>
.mt-2 {
  margin-top: 8px;
}
</style>
