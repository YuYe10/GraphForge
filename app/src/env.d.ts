// =============================================================================
// GraphForge — Environment Type Declarations
// GraphForge — 环境类型声明
// =============================================================================
//
// This module augments TypeScript's understanding of the runtime environment
// by declaring types for:
//
//   1. Vue Single-File Components (.vue) — Prevents TS errors when importing
//      .vue files in a Vite+Vue project. Each .vue file exports a
//      DefineComponent by default. (防止导入 .vue 文件时报 TS 错误)
//
//   2. ImportMeta / ImportMetaEnv — Typed access to Vite environment
//      variables prefixed with VITE_. Provides autocompletion and type
//      safety for `import.meta.env`. (为 Vite 环境变量提供类型安全访问)
//
//   3. Window extensions — Type-safe globals injected by Naive UI (message,
//      dialog, notification APIs) and the custom GraphForge theme system
//      (__graphforgeTheme). (为 Naive UI 全局 API 和图谱主题系统提供类型声明)
//
// =============================================================================

/// <reference types="vite/client" />

// ---------------------------------------------------------------------------
// Vue Single-File Component Module Declaration
// Vue 单文件组件模块声明
//
// Without this declaration, TypeScript would error on `import X from './X.vue'`
// because .vue files are not native TypeScript modules. This shim declares
// that every .vue file exports a standard Vue DefineComponent.
//
// 如果没有此声明，TypeScript 将无法识别 .vue 文件的导入。
// 此声明将所有 .vue 文件定义为标准的 Vue DefineComponent。
// ---------------------------------------------------------------------------
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// ---------------------------------------------------------------------------
// Vite Environment Variables (ImportMeta)
// Vite 环境变量类型定义
//
// Vite exposes env variables under `import.meta.env`. This interface
// documents all custom VITE_* variables used by the application.
// Variables are optional (?) by convention; Vite provides defaults at
// build time.
//
// Vite 将环境变量暴露在 `import.meta.env` 下。此接口记录了应用使用的
// 所有自定义 VITE_* 变量，按惯例均设为可选。
// ---------------------------------------------------------------------------

/**
 * Custom environment variables available via `import.meta.env`.
 * 通过 `import.meta.env` 访问的自定义环境变量。
 */
interface ImportMetaEnv {
  /** Base URL for the backend API (e.g., http://localhost:8080) */
  readonly VITE_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// ---------------------------------------------------------------------------
// Window (Global) Type Augmentations
// Window 全局对象类型扩展
//
// Naive UI injects helper methods onto the `window` object when its provider
// components (n-message-provider, n-dialog-provider, n-notification-provider)
// are mounted. These declarations provide TypeScript autocompletion and type
// safety when calling them in non-component code.
//
// Naive UI 会在其 Provider 组件挂载后向 window 对象注入辅助方法。
// 这些声明为在非组件代码中调用它们提供类型安全和自动补全。
// ---------------------------------------------------------------------------
interface Window {
  // -----------------------------------------------------------------------
  // Naive UI — $message API
  // 消息提示 API
  //
  // Provides toast-style notifications. Injected by <n-message-provider>.
  // 提供弹出式消息提示，由 <n-message-provider> 注入。
  // -----------------------------------------------------------------------
  $message?: {
    /** Display an error message / 显示错误消息 */
    error: (msg: string) => void
    /** Display a success message / 显示成功消息 */
    success: (msg: string) => void
    /** Display a warning message / 显示警告消息 */
    warning: (msg: string) => void
    /** Display an info message / 显示信息提示 */
    info: (msg: string) => void
    /** Display a loading message (optional, may not be present) */
    loading?: (msg: string) => void
  }

  // -----------------------------------------------------------------------
  // Naive UI — $dialog API
  // 对话框 API
  //
  // Provides modal dialog boxes. Injected by <n-dialog-provider>.
  // 提供模态对话框，由 <n-dialog-provider> 注入。
  // -----------------------------------------------------------------------
  $dialog?: {
    /** Display an info dialog / 显示信息对话框 */
    info: (opts: { title: string; content: string }) => void
    /** Display a warning dialog / 显示警告对话框 */
    warning: (opts: any) => void
    /** Display an error dialog / 显示错误对话框 */
    error: (opts: any) => void
    /** Display a success dialog / 显示成功对话框 */
    success: (opts: any) => void
  }

  // -----------------------------------------------------------------------
  // Naive UI — $notification API
  // 通知 API
  //
  // Provides notification cards. Injected by <n-notification-provider>.
  // 提供通知卡片，由 <n-notification-provider> 注入。
  // -----------------------------------------------------------------------
  $notification?: {
    /** Display an error notification / 显示错误通知 */
    error: (opts: any) => void
    /** Display a success notification / 显示成功通知 */
    success: (opts: any) => void
    /** Display a warning notification / 显示警告通知 */
    warning: (opts: any) => void
    /** Display an info notification / 显示信息通知 */
    info: (opts: any) => void
  }

  // -----------------------------------------------------------------------
  // GraphForge Custom — Theme System Global API
  // GraphForge 自定义主题系统全局 API
  //
  // Exposed on window so that non-Vue code (e.g., inline scripts, third-party
  // integrations) can read and toggle the application theme. The `mode` ref
  // enables reactive binding; `toggle` flips between 'light' and 'dark'.
  //
  // 暴露在 window 上，使非 Vue 代码（如内联脚本、第三方集成）也能读取和切换
  // 应用主题。`mode` 提供响应式绑定，`toggle` 在 'light' 和 'dark' 间切换。
  // -----------------------------------------------------------------------
  __graphforgeTheme?: {
    /** Reactive theme mode ref ('light' | 'dark') */
    mode: { value: string }
    /** Toggle between light and dark themes / 切换浅色/深色主题 */
    toggle: () => void
  }
}
