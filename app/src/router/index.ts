/**
 * GraphForge — Route Configuration
 * GraphForge — 路由配置
 *
 * Defines the single-page application routing tree, lazy-loaded view components,
 * i18n-aware document title resolution, and a global navigation guard that
 * updates the browser tab / document title on every route transition.
 *
 * 定义单页应用路由树、懒加载视图组件、支持 i18n 的文档标题解析，
 * 以及在每次路由切换时更新浏览器标签 / 页面标题的全局导航守卫。
 */

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import i18n from '@/i18n'

/**
 * Route table.
 * All child views are wrapped inside `MainLayout` and lazy-loaded via dynamic
 * `import()` for optimal chunk splitting.
 *
 * 路由表。所有子视图均包裹在 `MainLayout` 布局组件内，
 * 并通过动态 `import()` 懒加载以实现最佳代码分割。
 */
const routes: RouteRecordRaw[] = [
  {
    // Root path — loads the application shell / main layout
    // 根路径 — 加载应用外壳 / 主布局
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        // Dashboard — overview / home page
        // 仪表盘 — 概览 / 首页
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: 'dashboard.title' }
      },
      {
        // Knowledge Build — upload documents for processing
        // 知识构建 — 上传文档进行处理
        path: 'knowledge',
        name: 'KnowledgeBuild',
        component: () => import('@/views/Upload.vue'),
        meta: { title: 'knowledge.title' }
      },
      {
        // Documents — view and manage uploaded documents
        // 文档管理 — 查看和管理已上传的文档
        path: 'documents',
        name: 'Documents',
        component: () => import('@/views/Documents.vue'),
        meta: { title: 'documents.title' }
      },
      {
        // Knowledge Card — display extracted knowledge as cards
        // 知识卡片 — 以卡片形式展示提取的知识
        path: 'knowledge-card',
        name: 'KnowledgeCard',
        component: () => import('@/views/KnowledgeCard.vue'),
        meta: { title: 'knowledge_card.title' }
      },
      {
        // Graph — interactive knowledge graph visualization
        // 图谱 — 交互式知识图谱可视化
        path: 'graph',
        name: 'Graph',
        component: () => import('@/views/Graph.vue'),
        meta: { title: 'graph.title' }
      },
      {
        // Query — natural-language / SPARQL query interface
        // 查询 — 自然语言 / SPARQL 查询接口
        path: 'query',
        name: 'Query',
        component: () => import('@/views/Query.vue'),
        meta: { title: 'query.title' }
      },
      {
        // Status — processing job status / system health
        // 状态 — 处理任务状态 / 系统健康度
        path: 'status',
        name: 'Status',
        component: () => import('@/views/Status.vue'),
        meta: { title: 'status.title' }
      },
      {
        // Settings — user preferences and configuration
        // 设置 — 用户偏好与系统配置
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: 'settings.title' }
      }
    ]
  }
]

/**
 * Vue Router instance configured with HTML5 history mode (no hash).
 * Vue Router 实例，使用 HTML5 History 模式（无 hash）。
 */
const router = createRouter({
  history: createWebHistory(),
  routes
})

/**
 * Global before-each navigation guard.
 * 全局前置导航守卫。
 *
 * Resolves the i18n key stored in `to.meta.title`, translates it via
 * vue-i18n, and sets `document.title` to "{translated title} | {app name}".
 * This ensures every page has a meaningful, localised browser tab title.
 *
 * 解析 `to.meta.title` 中存储的 i18n 键，通过 vue-i18n 翻译后，
 * 将 `document.title` 设置为"{翻译后的标题} | {应用名称}"。
 * 确保每个页面都有有意义的、本地化的浏览器标签标题。
 */
router.beforeEach((to, _from, next) => {
  if (to.meta.title) {
    const t = i18n.global.t
    document.title = `${t(to.meta.title as string)} | ${t('app.page_title')}`
  }
  next()
})

export default router
