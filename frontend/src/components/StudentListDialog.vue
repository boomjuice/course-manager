<template>
  <el-dialog
    :model-value="visible"
    title="班内学生列表"
    width="600px"
    @close="$emit('update:visible', false)"
  >
    <el-table :data="students" border stripe>
      <el-table-column prop="name" label="姓名" />
      <el-table-column prop="parent_contact_info" label="家长联系方式" />
      <el-table-column label="标签">
        <template #default="scope">
          <el-tag
            v-for="tag in scope.row.tags"
            :key="tag.id"
            style="margin-right: 5px;"
            disable-transitions
          >
            {{ tag.name }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
    <template #footer>
      <el-button @click="$emit('update:visible', false)">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
defineProps<{
  visible: boolean;
  students: any[];
}>();

defineEmits(['update:visible']);
</script>
