<template>
  <el-dialog
    :model-value="visible"
    title="报名学生列表"
    width="500px"
    @close="handleClose"
  >
    <div v-if="!students || students.length === 0">暂无学生报名</div>
    <el-table v-else :data="students" style="width: 100%">
      <el-table-column prop="name" label="学生姓名" />
      <el-table-column prop="school" label="学校" />
      <el-table-column label="标签">
        <template #default="scope">
          <div class="tag-container">
            <el-tag
              v-for="tag in scope.row.tags"
              :key="tag.id"
              class="tag"
              :color="getTagColor(tag.subgroup)"
              style="color: white;"
            >
              {{ tag.subgroup ? `${tag.subgroup}: ${tag.item_value}` : tag.item_value }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
    </el-table>
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
import { getTagColor } from '@/utils/colors';

const props = defineProps<{
  visible: boolean;
  students: any[];
}>();

const emit = defineEmits(['update:visible']);

const handleClose = () => {
  emit('update:visible', false);
};

const groupedTags = (tags: any[]) => {
  if (!tags) return {};
  return tags.reduce((acc, tag) => {
    const group = tag.subgroup || '其他';
    if (!acc[group]) {
      acc[group] = [];
    }
    acc[group].push(tag);
    return acc;
  }, {});
};
</script>

<style scoped>
.tag-group {
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}
.subgroup-label {
  margin-right: 5px;
  font-weight: bold;
}
</style>
