<template>
  <el-dialog
    :model-value="visible"
    title="教师详情"
    width="500px"
    @close="$emit('update:visible', false)"
  >
    <el-descriptions v-if="teacher" :column="1" border>
      <el-descriptions-item label="姓名">{{ teacher.name }}</el-descriptions-item>
      <el-descriptions-item label="登录名">{{ teacher.user_name }}</el-descriptions-item>
      <el-descriptions-item label="联系方式">{{ teacher.contact_info }}</el-descriptions-item>
      <el-descriptions-item label="可教科目">
        <el-tag v-for="s in teacher.subjects" :key="s.id" class="detail-tag">{{ s.name }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="可教年级">
        <el-tag v-for="g in teacher.grades" :key="g.id" class="detail-tag" type="success">{{
            g.name
          }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="teacher.is_active ? 'success' : 'info'">
          {{ teacher.is_active ? '在职' : '离职' }}
        </el-tag>
      </el-descriptions-item>
    </el-descriptions>
    <div v-else>
      <p>暂无教师信息</p>
    </div>
    <template #footer>
      <el-button @click="$emit('update:visible', false)">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script lang="ts" setup>
defineProps<{
  visible: boolean;
  teacher: any;
}>();

defineEmits(['update:visible']);
</script>

<style scoped>
.detail-tag {
  margin-right: 5px;
}
</style>
