<template>
  <el-dialog
    :model-value="visible"
    title="报名记录列表"
    width="700px"
    @close="handleClose"
  >
    <el-table :data="enrollments" stripe>
      <el-table-column prop="display_name" label="报名记录" />
    </el-table>
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
const props = defineProps<{
  visible: boolean;
  enrollments: any[];
}>();

const emit = defineEmits(['update:visible']);

const handleClose = () => {
  emit('update:visible', false);
};
</script>
