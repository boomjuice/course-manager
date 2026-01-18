/**
 * Pinia Store Entry Point
 */
import { createPinia } from 'pinia'

export const pinia = createPinia()

export * from './auth'
export * from './permission'
