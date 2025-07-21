<template>
  <el-dialog
    :model-value="visible"
    title="开班计划详情"
    width="600px"
    @close="handleClose"
  >
    <div v-if="!offering">加载中...</div>
    <el-descriptions v-else :column="2" border>
      <el-descriptions-item label="计划名称">{{ offering.name }}</el-descriptions-item>
      <el-descriptions-item label="课程产品">{{ offering.course_product.display_name }}</el-descriptions-item>
      <el-descriptions-item label="开始日期">{{ offering.start_date }}</el-descriptions-item>
      <el-descriptions-item label="结束日期">{{ offering.end_date }}</el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="getStatusTagType(offering.status)">{{ getStatusText(offering.status) }}</el-tag>
      </el-descriptions-item>
    </el-descriptions>
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
const props = defineProps<{
  visible: boolean;
  offering: any;
}>();

const emit = defineEmits(['update:visible']);

const handleClose = () => {
  emit('update:visible', false);
};

const getStatusText = (status: string) => {
  const map = { planning: '计划中', open: '报名中', in_progress: '已开课', completed: '已结束' };
  return map[status] || '未知';
};

const getStatusTagType = (status: string) => {
  const map = { planning: 'info', open: 'success', in_progress: 'primary', completed: 'warning' };
  return map[status] || 'info';
};
</script>
