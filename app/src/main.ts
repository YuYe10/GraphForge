// =============================================================================
// GraphForge — Application Entry Point
// GraphForge — 应用入口文件
// =============================================================================
//
// This module bootstraps the Vue 3 application by:
// - Creating the Vue app instance (创建 Vue 应用实例)
// - Registering core plugins: Pinia (state), Vue Router (routing), vue-i18n
//   (internationalization), and Naive UI (component library)
// - Installing global custom directives (e.g., v-ripple)
// - Injecting runtime meta tags required by Naive UI for proper SSR-style
//   resolution in SPA mode
// - Mounting the app to the DOM
//
// Core plugins (核心插件):
//   Pinia  — Lightweight state management (轻量级状态管理)
//   Router — File-based / declarative routing (文件式/声明式路由)
//   i18n   — Internationalization with Chinese & English (国际化，支持中英文)
//   Naive  — Vue 3 UI component library (Vue 3 UI 组件库)
//
// =============================================================================

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import { vRipple } from './directives/ripple'
import './styles/main.scss'

// ---------------------------------------------------------------------------
// Create the Vue application instance
// 创建 Vue 应用实例
// ---------------------------------------------------------------------------
const app = createApp(App)

// ---------------------------------------------------------------------------
// Naive UI Style Resolution Meta Tag
// Naive UI 样式解析 Meta 标签
//
// Naive UI requires a <meta name="naive-ui-style"> tag to be present in the
// <head> when used in SPA mode (without SSR). This ensures the component
// library's CSS variables and reset styles resolve correctly. This tag is
// created programmatically rather than hard-coded in index.html to keep the
// entry point self-contained.
//
// Naive UI 在 SPA 模式下需要一个名为 "naive-ui-style" 的 meta 标签，
// 以确保组件库的 CSS 变量和重置样式正确解析。
// 此处通过 JavaScript 动态创建，保持入口文件的独立性。
// ---------------------------------------------------------------------------
const meta = document.createElement('meta')
meta.name = 'naive-ui-style'
document.head.appendChild(meta)

// ---------------------------------------------------------------------------
// Plugin Registration (插件注册)
// ---------------------------------------------------------------------------

// Pinia — Reactive state management store (响应式状态管理)
app.use(createPinia())

// Vue Router — Client-side routing (客户端路由)
app.use(router)

// vue-i18n — Internationalization (国际化)
app.use(i18n)

// Naive UI — UI component library (UI 组件库)
app.use(naive)

// ---------------------------------------------------------------------------
// Global Custom Directives (全局自定义指令)
// ---------------------------------------------------------------------------

// v-ripple — Material-inspired ripple effect on click
//           点击时的 Material 风格水波纹效果
app.directive('ripple', vRipple)

// ---------------------------------------------------------------------------
// Mount the application to the DOM
// 将应用挂载到 DOM
// ---------------------------------------------------------------------------
app.mount('#app')
