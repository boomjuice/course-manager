<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<template>
  <div class="placeholder-view">
    <div class="page-header">
      <h1>{{ title }}</h1>
    </div>
    <el-alert
      :title="`${title}功能开发中`"
      :description="description || '此功能正在开发中，敬请期待。'"
      type="info"
      show-icon
    />
  </div>
</template>
