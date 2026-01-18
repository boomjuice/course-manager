<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<template>
  <div class="not-found">
    <h1>404</h1>
    <p>页面不存在</p>
    <el-button type="primary" @click="goHome">返回首页</el-button>
  </div>
</template>

<style scoped lang="scss">
.not-found {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);

  h1 {
    font-size: 96px;
    font-weight: 600;
    color: var(--primary-500);
    margin-bottom: var(--spacing-md);
  }

  p {
    font-size: 18px;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xl);
  }
}
</style>
