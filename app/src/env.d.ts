/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Naive UI global API types
interface Window {
  $message?: {
    error: (msg: string) => void
    success: (msg: string) => void
    warning: (msg: string) => void
    info: (msg: string) => void
    loading?: (msg: string) => void
  }
  $dialog?: {
    info: (opts: { title: string; content: string }) => void
    warning: (opts: any) => void
    error: (opts: any) => void
    success: (opts: any) => void
  }
  $notification?: {
    error: (opts: any) => void
    success: (opts: any) => void
    warning: (opts: any) => void
    info: (opts: any) => void
  }
  __graphforgeTheme?: {
    mode: { value: string }
    toggle: () => void
  }
}
