// ============================================================================
// GraphForge - Vite Build Configuration
// GraphForge Vite 构建配置
//
// Key features:
//   - Vue 3 + TypeScript SFC compilation
//   - Auto-import for Vue/Vue Router/Pinia APIs + Naive UI components
//   - Path alias (@ -> src/) for cleaner imports
//   - Dev server on port 3000 with /api proxy to backend (port 8000)
//   - Vue DevTools integration for debugging
// ============================================================================

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { NaiveUiResolver } from 'unplugin-vue-components/resolvers'
import VueDevTools from 'vite-plugin-vue-devtools'

export default defineConfig({
  plugins: [
    vue(),              // Vue 3 SFC support（Vue 3 单文件组件支持）
    VueDevTools(),      // Vue DevTools during development（开发工具集成）

    // ---------------------------------------------------------------
    // Auto-import: automatically imports Vue/Router/Pinia/NaiveUI APIs
    // 自动导入：无需手动 import 即可使用 Vue/Router/Pinia/NaiveUI API
    // ---------------------------------------------------------------
    AutoImport({
      imports: [
        'vue',          // ref, reactive, computed, onMounted, etc.
        'vue-router',   // useRoute, useRouter
        'pinia',        // defineStore, storeToRefs
        {
          'naive-ui': [
            'useDialog',
            'useMessage',
            'useNotification',
            'useLoadingBar'
          ]
        }
      ],
      dts: 'src/auto-imports.d.ts'  // Generated type declarations
    }),

    // ---------------------------------------------------------------
    // Auto-register: automatically registers Naive UI components
    // 自动注册：无需手动 import 即可使用 Naive UI 组件
    // ---------------------------------------------------------------
    Components({
      resolvers: [NaiveUiResolver()],
      dts: 'src/components.d.ts'  // Generated component type declarations
    })
  ],

  // ---------------------------------------------------------------
  // Path resolution: @ alias -> src/ directory
  // 路径解析：@ 别名映射到 src/ 目录
  // ---------------------------------------------------------------
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },

  // ---------------------------------------------------------------
  // Dev server configuration
  // 开发服务器配置
  // ---------------------------------------------------------------
  server: {
    port: 3000,  // Dev server port（开发服务器端口）
    proxy: {
      // Proxy /api/* requests to the FastAPI backend
      // 将 /api/* 请求代理到 FastAPI 后端
      '/api': {
        target: process.env.VITE_API_BASE || 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})

