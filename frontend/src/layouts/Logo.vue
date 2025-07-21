<template>
  <div class="logo-container">
    <router-link to="/">
      <img src="@/assets/logo.svg" alt="Logo" class="logo-img">
      <h1 class="logo-title">课程管理系统</h1>
    </router-link>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #ffffff;
  border-bottom: 1px solid #ebeef5;
}

.logo-container a {
  display: flex;
  align-items: center;
  text-decoration: none;
  color: inherit;
}

.logo-img {
  height: 32px;
  width: 32px;
  margin-right: 12px;
}

.logo-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #303133;
}
</style>
