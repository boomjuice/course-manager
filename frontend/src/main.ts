/**
 * Application Entry Point
 */
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
// @ts-ignore - Element Plus locale type
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import { pinia, useAuthStore, usePermissionStore } from './stores'
import { registerPermissionDirectives } from './directives'
import './styles/index.scss'

async function bootstrap() {
  const app = createApp(App)

  // Register Element Plus
  app.use(ElementPlus, {
    locale: zhCn
  })

  // Register Element Plus Icons
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  // Register Pinia
  app.use(pinia)

  // Register permission directives (v-permission, v-permission-disabled)
  registerPermissionDirectives(app)

  // Initialize auth store
  const authStore = useAuthStore()
  await authStore.initialize()

  // Load user permissions if authenticated
  if (authStore.isAuthenticated) {
    const permissionStore = usePermissionStore()
    try {
      await permissionStore.loadPermissions()
    } catch (error) {
      console.error('Failed to load permissions:', error)
    }
  }

  // Register Router
  app.use(router)

  // Mount app
  app.mount('#app')
}

bootstrap()
