<template>
  <el-dialog
    :model-value="visible"
    title="学生详情"
    width="500px"
    @close="handleClose"
  >
    <div v-if="student" class="detail-content">
      <p><strong>姓名:</strong> {{ student.name }}</p>
      <p><strong>学校:</strong> {{ student.school || '-' }}</p>
      <p><strong>年级:</strong> {{ student.grade ? student.grade.item_value : '-' }}</p>
      <p><strong>家长联系方式:</strong> {{ student.parent_contact_info || '-' }}</p>
      <p><strong>备注:</strong> {{ student.notes || '-' }}</p>
      <div>
        <strong>标签:</strong>
        <div class="tag-container">
          <el-tag 
            v-for="tag in student.tags" 
            :key="tag.id" 
            class="detail-tag"
            :color="getTagColor(tag.subgroup)"
            style="color: white;"
          >
            {{ tag.subgroup ? `${tag.subgroup}: ${tag.item_value}` : tag.item_value }}
          </el-tag>
        </div>
      </div>
    </div>
    <div v-else>加载中...</div>
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { getTagColor } from '@/utils/colors';

const props = defineProps<{
  visible: boolean;
  student: any;
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
.tag-container {
  margin-top: 5px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.detail-tag {
  margin: 0;
}
</style>
