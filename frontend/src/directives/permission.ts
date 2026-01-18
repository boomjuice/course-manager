/**
 * v-permission 指令
 *
 * 用法:
 * - v-permission="['student', 'read']" 需要student:read权限
 * - v-permission="['student', 'edit']" 需要student:edit权限
 * - v-permission="['student', 'delete']" 需要student:delete权限
 *
 * 无权限时元素会被移除
 */
import type { Directive, DirectiveBinding } from 'vue'
import { usePermissionStore } from '@/stores/permission'
import type { ResourceCode, PermissionAction } from '@/types/permission'

export type PermissionValue = [ResourceCode, PermissionAction]

export const vPermission: Directive<HTMLElement, PermissionValue> = {
  mounted(el: HTMLElement, binding: DirectiveBinding<PermissionValue>) {
    const { value } = binding

    if (!value || !Array.isArray(value) || value.length !== 2) {
      console.warn('[v-permission] Invalid value format. Expected [resource, action]')
      return
    }

    const [resource, action] = value
    const permissionStore = usePermissionStore()

    // 检查权限
    const hasPermission = permissionStore.hasPermission(resource, action)

    if (!hasPermission) {
      // 无权限，移除元素
      el.parentNode?.removeChild(el)
    }
  },

  updated(el: HTMLElement, binding: DirectiveBinding<PermissionValue>) {
    const { value, oldValue } = binding

    // 值未变化，不处理
    if (JSON.stringify(value) === JSON.stringify(oldValue)) {
      return
    }

    if (!value || !Array.isArray(value) || value.length !== 2) {
      return
    }

    const [resource, action] = value
    const permissionStore = usePermissionStore()

    const hasPermission = permissionStore.hasPermission(resource, action)

    if (!hasPermission) {
      el.parentNode?.removeChild(el)
    }
  }
}

/**
 * v-permission-disabled 指令
 *
 * 用法:
 * - v-permission-disabled="['student', 'edit']"
 *
 * 无权限时元素会被禁用而不是移除（适用于按钮等需要保留但禁用的场景）
 */
export const vPermissionDisabled: Directive<HTMLElement, PermissionValue> = {
  mounted(el: HTMLElement, binding: DirectiveBinding<PermissionValue>) {
    const { value } = binding

    if (!value || !Array.isArray(value) || value.length !== 2) {
      console.warn('[v-permission-disabled] Invalid value format. Expected [resource, action]')
      return
    }

    const [resource, action] = value
    const permissionStore = usePermissionStore()

    const hasPermission = permissionStore.hasPermission(resource, action)

    if (!hasPermission) {
      // 无权限，禁用元素
      el.setAttribute('disabled', 'disabled')
      el.classList.add('is-disabled')
      el.style.pointerEvents = 'none'
      el.style.opacity = '0.5'
    }
  },

  updated(el: HTMLElement, binding: DirectiveBinding<PermissionValue>) {
    const { value, oldValue } = binding

    if (JSON.stringify(value) === JSON.stringify(oldValue)) {
      return
    }

    if (!value || !Array.isArray(value) || value.length !== 2) {
      return
    }

    const [resource, action] = value
    const permissionStore = usePermissionStore()

    const hasPermission = permissionStore.hasPermission(resource, action)

    if (!hasPermission) {
      el.setAttribute('disabled', 'disabled')
      el.classList.add('is-disabled')
      el.style.pointerEvents = 'none'
      el.style.opacity = '0.5'
    } else {
      el.removeAttribute('disabled')
      el.classList.remove('is-disabled')
      el.style.pointerEvents = ''
      el.style.opacity = ''
    }
  }
}

/**
 * 注册所有权限指令
 */
export function registerPermissionDirectives(app: ReturnType<typeof import('vue').createApp>) {
  app.directive('permission', vPermission)
  app.directive('permission-disabled', vPermissionDisabled)
}
