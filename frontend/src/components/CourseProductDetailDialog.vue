<template>
  <el-dialog
    :model-value="visible"
    title="课程产品详情"
    width="500px"
    @close="handleClose"
  >
    <div v-if="product" class="detail-content">
      <p><strong>产品名称:</strong> {{ product.name }}</p>
      <p><strong>科目:</strong> {{ product.subject }}</p>
      <p><strong>年级:</strong> {{ product.grade }}</p>
      <p><strong>课程类型:</strong> {{ product.course_type }}</p>
      <p><strong>标准课长(分钟):</strong> {{ product.duration_minutes }}</p>
    </div>
    <div v-else>加载中...</div>
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
const props = defineProps<{
  visible: boolean;
  product: any;
}>();

const emit = defineEmits(['update:visible']);

const handleClose = () => {
  emit('update:visible', false);
};
</script>

<style scoped>
.detail-content p {
  margin-bottom: 10px;
}
</style>
