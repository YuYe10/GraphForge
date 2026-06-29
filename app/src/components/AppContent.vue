<!--
  ============================================================================
  AppContent.vue — Application Root / 应用根组件
  ============================================================================
  Role:
    This is the root layout component of the GraphForge application. It wraps
    the entire app in a minimal container and renders the current route via
    <router-view>. It also serves as the **bootstrap point** for Naive UI
    imperative APIs — mounting $message, $dialog, and $notification onto the
    global `window` object so they can be used outside of Vue's composition
    context (e.g., in Pinia stores or utility modules).

    这是 GraphForge 应用的根布局组件。它用最简容器包裹整个应用，通过
    <router-view> 渲染当前路由。同时充当 **Naive UI 命令式 API 的引导点** —
    将 $message、$dialog、$notification 挂载到全局 `window` 对象上，使其可
    在 Vue 组合式上下文之外（例如 Pinia store 或工具模块）使用。
  ============================================================================
-->

<template>
  <!--
    Root application container / 应用根容器
    - id="app" is used by Vue's mount target.
    - class="app-container" provides full-viewport sizing.
  -->
  <div id="app" class="app-container">
    <!--
      Route outlet / 路由出口
      All pages rendered by vue-router appear here.
      所有由 vue-router 渲染的页面都在此处呈现。
    -->
    <router-view />
  </div>
</template>

<script setup lang="ts">
/**
 * ============================================================================
 * AppContent — Naive UI Bootstrap Script / Naive UI 引导脚本
 * ============================================================================
 *
 * This script runs once when the component is mounted. It calls the Naive UI
 * hooks `useMessage`, `useDialog`, and `useNotification` inside a Vue
 * component's setup context (the only context where these hooks work), then
 * stores the returned instances on `window` for global access.
 *
 * 该脚本在组件挂载时运行一次。它在 Vue 组件的 setup 上下文（这些 hooks
 * 唯一有效的上下文）中调用 Naive UI 的 `useMessage`、`useDialog` 和
 * `useNotification` hooks，然后将返回的实例存储到 `window` 上以实现全局访问。
 *
 * Why this is needed / 为什么需要这样做:
 * - Naive UI's imperative APIs require being called within a Vue component's
 *   setup lifecycle; they fail if called from a plain TS module.
 * - By mounting them here, any module can do:
 *     window.$message.success('Hello')
 *   without being inside a <script setup> block.
 * - Naive UI 的命令式 API 要求在 Vue 组件的 setup 生命周期内调用；
 *   如果从普通 TS 模块调用则会失败。
 * - 通过在此处挂载，任何模块都可以执行 `window.$message.success('Hello')`，
 *   而无需位于 <script setup> 块内。
 */
import { useMessage, useDialog, useNotification } from 'naive-ui'

// Mount Naive UI imperative API instances onto the global window object.
// 将 Naive UI 命令式 API 实例挂载到全局 window 对象上。
window.$message = useMessage()
window.$dialog = useDialog()
window.$notification = useNotification()
</script>

<style scoped>
/**
 * App container styles / 应用容器样式
 * Provides full-viewport sizing for the root element.
 * 为根元素提供全视口尺寸。
 */
.app-container {
  min-height: 100vh;
  width: 100%;
}
</style>
