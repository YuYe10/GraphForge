<!-- ==========================================================================
  MainLayout — Primary Application Layout / 主应用布局
  ==========================================================================

  This is the shell layout wrapping all routed views. It provides:
  本布局作为所有路由视图的外层壳，提供以下功能：

  Template Structure / 模板结构:
    1. layout-bg          — Animated gradient background / 动态渐变背景
    2. n-layout-header    — Sticky glassmorphism header with logo, search, nav, actions
                           粘性毛玻璃效果头部，包含 Logo、搜索、导航、操作按钮
    3. breadcrumb-bar     — Contextual breadcrumb navigation / 上下文面包屑导航
    4. n-layout-content   — Router view with page transition animations / 带页面过渡动画的路由视图
    5. processing-floater — Global task progress floating widget / 全局任务进度浮动组件
    6. CommandPalette     — Ctrl+K command palette / Ctrl+K 命令面板

  Features / 核心功能:
    - Theme toggling (dark/light) persisted in localStorage / 深色/浅色主题切换，持久化到 localStorage
    - Language switching (zh/en) via appStore / 通过 appStore 进行中英文切换
    - Global keyboard shortcuts (Ctrl+K, Escape) / 全局键盘快捷键
    - Responsive navigation menu / 响应式导航菜单
    - Dynamic breadcrumb generation / 动态面包屑生成
    - Glassmorphism visual effects / 毛玻璃视觉效果

  Dependencies / 依赖:
    - Naive UI (n-layout, n-layout-header, n-button, n-icon, n-dropdown, n-badge, etc.)
    - Vue Router (useRoute, useRouter)
    - vue-i18n (useI18n for t() and locale)
    - Pinia stores: appStore, processingStore
    - IonIcons5 via @vicons/ionicons5
-->

<template>
  <n-layout class="main-layout">
    <!-- ============================================================
         Animated Gradient Background / 动态渐变背景层
         ============================================================
         Three radial gradients positioned at different corners create
         a subtle ambient glow effect behind the content.
         三个位于不同角落的径向渐变在内容下方营造微弱的氛围光效。 -->
    <div class="layout-bg"></div>

    <!-- ============================================================
         Sticky Header with Glassmorphism / 粘性毛玻璃头部
         ============================================================
         Uses backdrop-filter blur with a semi-transparent background
         to achieve the frost-glass aesthetic. Stays fixed at the top
         with z-index 1000 to layer above all content.
         使用 backdrop-filter 模糊和半透明背景实现磨砂玻璃效果。
         固定在顶部，z-index 为 1000，层叠在所有内容之上。 -->
    <n-layout-header bordered class="header glass-strong">
      <div class="header-inner">
        <!-- Logo Section / Logo 区域 -->
        <!-- Clicking the logo navigates to the root route ("/") -->
        <!-- 点击 Logo 跳转到根路由 -->
        <div class="header-logo" @click="$router.push('/')">
          <div class="logo-icon animate-float">
            <n-icon size="28"><cube-outline /></n-icon>
          </div>
          <div class="logo-text">
            <h2 class="logo-title gradient-text-gold">{{ t('app.title') }}</h2>
          </div>
        </div>

        <!-- Search Bar / 全局搜索栏 -->
        <!-- Currently a UI placeholder; search functionality is TBD -->
        <!-- 当前为 UI 占位，搜索功能待实现 -->
        <div class="header-search">
          <n-input
            round
            clearable
            placeholder="搜索节点、文档、概念..."
            :style="{ width: '320px' }"
          >
            <template #prefix>
              <n-icon><search-outline /></n-icon>
            </template>
          </n-input>
        </div>

        <!-- Navigation Menu / 顶部导航菜单 -->
        <!-- Rendered from the reactive menuOptions computed property.
             The active item is highlighted with a gold gradient background
             and a bottom indicator bar. -->
        <!-- 从响应式 menuOptions 计算属性渲染。活动项以金色渐变背景
             和底部指示条高亮。 -->
        <div class="header-nav">
          <div
            v-for="item in menuOptions"
            :key="item.key"
            :class="['nav-item', { active: activeKey === item.key || activeKey.startsWith(item.key + '/') }]"
            @click="handleMenuSelect(item.key)"
          >
            <n-icon v-if="item.icon" size="16">
              <component :is="item.icon" />
            </n-icon>
            <span>{{ item.label }}</span>
            <!-- Active indicator: a thin gradient bar beneath the active nav item -->
            <!-- 活动指示器：活动导航项下方的细渐变条 -->
            <div v-if="activeKey === item.key || activeKey.startsWith(item.key + '/')" class="nav-indicator"></div>
          </div>
        </div>

        <!-- Right Actions / 右侧操作区 -->
        <div class="header-right">
          <n-space :size="8" align="center">
            <!-- Theme Toggle Button / 主题切换按钮 -->
            <!-- Shows a sun icon in dark mode (meaning "switch to light")
                 and a moon icon in light mode (meaning "switch to dark") -->
            <!-- 深色模式下显示太阳图标（意为"切换到浅色"），
                 浅色模式下显示月亮图标（意为"切换到深色"） -->
            <n-button text circle @click="toggleTheme" class="header-btn">
              <template #icon>
                <n-icon size="18">
                  <sunny-outline v-if="themeMode === 'dark'" />
                  <moon-outline v-else />
                </n-icon>
              </template>
            </n-button>

            <!-- Language Selector / 语言选择器 -->
            <!-- Hover-triggered dropdown with zh/en options.
                 Selection is handled by handleLanguageChange. -->
            <!-- 悬停触发的下拉菜单，提供中文/英文选项，选择由 handleLanguageChange 处理 -->
            <n-dropdown trigger="hover" :options="languageOptions" @select="handleLanguageChange">
              <n-button text class="header-btn">
                <template #icon>
                  <n-icon size="18"><globe-outline /></n-icon>
                </template>
                <span class="lang-label">{{ currentLangLabel }}</span>
              </n-button>
            </n-dropdown>

            <!-- Notification Badge / 通知徽标 -->
            <!-- Displays the count of active processing jobs.
                 Clicking opens the processing floater widget. -->
            <!-- 显示正在处理的任务数量，点击打开处理进度浮动组件 -->
            <n-badge :value="processingStore.processingCount" :max="99" :show-zero="false" processing>
              <n-button text circle class="header-btn" @click="processingStore.showFloater()">
                <template #icon>
                  <n-icon size="20"><notifications-outline /></n-icon>
                </template>
              </n-button>
            </n-badge>

            <!-- User Menu / 用户菜单 -->
            <!-- Hover-triggered dropdown with profile, settings, logout.
                 Uses a placeholder avatar image. -->
            <!-- 悬停触发的下拉菜单，包含个人资料、设置、登出。
                 头像使用占位图片。 -->
            <n-dropdown trigger="hover" :options="userMenuOptions" @select="handleUserMenuSelect">
              <n-button text class="header-btn user-btn">
                <n-avatar round :size="34" src="https://07akioni.oss-cn-beijing.aliyuncs.com/07akioni.jpeg" />
              </n-button>
            </n-dropdown>
          </n-space>
        </div>
      </div>
    </n-layout-header>

    <!-- ============================================================
         Breadcrumb Bar / 面包屑导航条
         ============================================================
         Dynamically generated based on the current route path.
         Only visible when there is more than one breadcrumb item
         (i.e., the user has navigated deeper than the home page).
         Non-last items are clickable for navigation.
         根据当前路由路径动态生成，当深度超过首页时显示。
         非最后一项可点击跳转。 -->
    <div v-if="breadcrumbs.length > 1" class="breadcrumb-bar">
      <n-breadcrumb>
        <n-breadcrumb-item
          v-for="(crumb, idx) in breadcrumbs"
          :key="idx"
          @click="idx < breadcrumbs.length - 1 && $router.push(crumb.path)"
        >
          {{ crumb.label }}
        </n-breadcrumb-item>
      </n-breadcrumb>
    </div>

    <!-- ============================================================
         Main Content Area / 主内容区域
         ============================================================
         Wraps the router-view with a fade-slide transition.
         The transition uses different easing curves for enter
         (slower, bouncier) and leave (faster) to create a polished UX.
         使用 fade-slide 过渡动画包裹 router-view。
         进入和离开使用不同的缓动曲线，营造精致的用户体验。 -->
    <n-layout>
      <n-layout-content :native-scrollbar="false" class="main-content">
        <div class="content-wrapper">
          <router-view v-slot="{ Component, route: r }">
            <transition name="fade-slide" mode="out-in">
              <component :is="Component" :key="r.path" />
            </transition>
          </router-view>
        </div>
      </n-layout-content>
    </n-layout>

    <!-- Global Processing Floater / 全局处理进度浮动组件 -->
    <!-- A floating widget showing real-time ingestion/processing task progress.
         Toggled via processingStore.showFloater(). -->
    <!-- 展示实时摄取/处理任务进度的浮动组件，通过 processingStore.showFloater() 切换显示 -->
    <processing-floater />

    <!-- Command Palette (Ctrl+K) / 命令面板（Ctrl+K 触发） -->
    <!-- A spotlight-style command search overlay inspired by VS Code's
         command palette. Visibility is controlled by the showCommandPalette ref
         and the Ctrl+K / Escape keyboard shortcuts. -->
    <!-- 类 VS Code 命令面板的聚光灯式命令搜索覆盖层。
         显示状态由 showCommandPalette 引用控制，通过 Ctrl+K 和 Escape 切换。 -->
    <CommandPalette v-model:visible="showCommandPalette" />
  </n-layout>
</template>

<script setup lang="ts">
/**
 * Main Layout — Script Setup / 主布局脚本
 * =========================================
 *
 * Composition API script setup using Vue 3's <script setup> syntactic sugar.
 * All logic is declared at the top level and compiled into component setup().
 *
 * 使用 Vue 3 的 <script setup> 语法糖，所有逻辑在顶层声明并编译为 setup() 函数。
 */

import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useProcessingStore } from '@/stores/processing'
import ProcessingFloater from '@/components/ProcessingFloater.vue'
import CommandPalette from '@/components/CommandPalette.vue'
import {
  CubeOutline, GlobeOutline, NotificationsOutline,
  SearchOutline, SunnyOutline, MoonOutline,
  GridOutline, CloudUploadOutline, DocumentTextOutline,
  GitNetworkOutline, CodeSlashOutline, TimeOutline,
  OptionsOutline
} from '@vicons/ionicons5'

// ---- Router & State / 路由与状态 ----
const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const appStore = useAppStore()
const processingStore = useProcessingStore()

/**
 * Currently active navigation key, derived from the current route path.
 * 当前活动的导航键，从当前路由路径派生。
 * Used to highlight the active nav item in the header menu.
 * 用于高亮头部菜单中的活动导航项。
 */
const activeKey = ref(route.path)

/**
 * Theme mode state, initialized from localStorage with 'light' as default.
 * 主题模式状态，从 localStorage 初始化，默认为 'light'。
 * Persisted on every toggle via toggleTheme().
 * 每次通过 toggleTheme() 切换时持久化。
 */
const themeMode = ref(localStorage.getItem('graphforge-theme') || 'light')

/**
 * Command palette visibility state.
 * 命令面板显示状态。
 * Controlled by Ctrl+K / Cmd+K toggle and Escape to close.
 * 由 Ctrl+K/Cmd+K 切换和 Escape 关闭控制。
 */
const showCommandPalette = ref(false)

/**
 * ========================================
 * Global Keyboard Shortcuts / 全局键盘快捷键
 * ========================================
 *
 * Registers document-level keydown listener in onMounted and removes it
 * in onUnmounted to prevent leaks.
 *
 * 在 onMounted 中注册文档级 keydown 监听器，在 onUnmounted 中移除以防止泄漏。
 *
 * Shortcuts / 快捷键:
 *   Ctrl+K / Cmd+K  — Toggle command palette / 切换命令面板
 *   Escape          — Close command palette / 关闭命令面板
 */
const handleGlobalKeydown = (e: KeyboardEvent) => {
  // Ctrl+K (Windows/Linux) or Cmd+K (macOS): toggle command palette
  // Ctrl+K (Windows/Linux) 或 Cmd+K (macOS): 切换命令面板
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    showCommandPalette.value = !showCommandPalette.value
  }
  // Escape: close command palette (only when visible)
  // Escape: 关闭命令面板（仅当可见时）
  if (e.key === 'Escape' && showCommandPalette.value) {
    showCommandPalette.value = false
  }
}

/**
 * ========================================
 * Theme Toggling / 主题切换
 * ========================================
 *
 * Toggles between 'dark' and 'light' modes. The preference is persisted
 * in localStorage under the key 'graphforge-theme' and also propagated
 * to the global __graphforgeTheme object (used by external theme-aware
 * components) and the document's <html> element CSS class.
 *
 * 在 'dark' 和 'light' 模式间切换。偏好通过键 'graphforge-theme'
 * 持久化到 localStorage，并同步到全局 __graphforgeTheme 对象
 * （供外部感知主题的组件使用）以及文档 <html> 元素的 CSS 类。
 */
const toggleTheme = () => {
  themeMode.value = themeMode.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem('graphforge-theme', themeMode.value)
  // Sync with the global theme instance if it exists
  // 如果全局主题实例存在，同步状态
  if ((window as any).__graphforgeTheme) {
    (window as any).__graphforgeTheme.mode.value = themeMode.value
  }
  // Toggle the 'dark' class on <html> element for CSS variable switching
  // 切换 <html> 元素上的 'dark' CSS 类以切换 CSS 变量
  document.documentElement.classList.toggle('dark', themeMode.value === 'dark')
}

/**
 * ========================================
 * Navigation Menu Configuration / 导航菜单配置
 * ========================================
 *
 * Computed menu items with i18n labels and IonIcons icons.
 * The menu is reactive: labels update automatically when the locale changes.
 *
 * 包含国际化标签和 IonIcons 图标的计算属性菜单项。
 * 菜单是响应式的：语言切换时标签自动更新。
 */
const menuOptions = computed(() => [
  { label: t('navigation.dashboard'), key: '/', icon: GridOutline },
  { label: t('navigation.knowledge_build'), key: '/knowledge', icon: CloudUploadOutline },
  { label: '文档管理', key: '/documents', icon: DocumentTextOutline },
  { label: t('navigation.knowledge_card'), key: '/knowledge-card', icon: OptionsOutline },
  { label: t('navigation.graph_visualization'), key: '/graph', icon: GitNetworkOutline },
  { label: t('navigation.query'), key: '/query', icon: CodeSlashOutline },
  { label: t('navigation.status'), key: '/status', icon: TimeOutline }
])

/**
 * ========================================
 * Breadcrumb Generation / 面包屑生成
 * ========================================
 *
 * Dynamically builds breadcrumb path based on the current route.
 * Always starts with a "Home" (首页) entry pointing to "/".
 * If the current route matches a menu item prefix, appends that item
 * as the second breadcrumb.
 *
 * 根据当前路由动态构建面包屑路径。始终以指向 "/" 的 "首页" 开始。
 * 如果当前路由匹配某个菜单项前缀，则将该菜单项作为第二个面包屑追加。
 *
 * Example / 示例:
 *   Route /graph           -> [首页, Graph Visualization]
 *   Route /knowledge-card  -> [首页, Knowledge Cards]
 */
const breadcrumbs = computed(() => {
  const crumbs: { label: string; path: string }[] = [{ label: '首页', path: '/' }]
  const menuItem = menuOptions.value.find(m => m.key !== '/' && route.path.startsWith(m.key))
  if (menuItem) crumbs.push({ label: menuItem.label, path: menuItem.key })
  return crumbs
})

/**
 * ========================================
 * Language Switching / 语言切换
 * ========================================
 */

/** Display label for the currently selected language / 当前选中语言的显示标签 */
const currentLangLabel = computed(() => locale.value === 'zh' ? '中文' : 'English')

/** Language dropdown options / 语言下拉菜单选项 */
const languageOptions = [
  { label: '中文', key: 'zh' },
  { label: 'English', key: 'en' }
]

/**
 * ========================================
 * User Menu Configuration / 用户菜单配置
 * ========================================
 *
 * Computed user menu items with i18n labels.
 * 包含国际化标签的计算属性用户菜单项。
 */
const userMenuOptions = computed(() => [
  { label: t('common.profile'), key: 'profile' },
  { label: t('common.settings'), key: 'settings' },
  { type: 'divider' as const },
  { label: t('common.logout'), key: 'logout' }
])

/**
 * ========================================
 * Event Handlers / 事件处理函数
 * ========================================
 */

/**
 * Handles navigation menu item selection.
 * 处理导航菜单项选择。
 * Updates the active key and navigates to the selected route.
 * 更新活动键并跳转到选中路由。
 */
const handleMenuSelect = (key: string) => {
  activeKey.value = key
  router.push(key)
}

/**
 * Handles language selection from the dropdown.
 * 处理下拉菜单的语言选择。
 * Updates both the Pinia appStore and the vue-i18n locale ref.
 * The appStore.setLanguage() also persists the preference to localStorage.
 * 同时更新 Pinia appStore 和 vue-i18n 的 locale 引用。
 * appStore.setLanguage() 还会将偏好持久化到 localStorage。
 */
const handleLanguageChange = (key: string) => {
  appStore.setLanguage(key as 'zh' | 'en')
  locale.value = key as 'zh' | 'en'
}

/**
 * Handles user menu selection (profile, settings, logout).
 * 处理用户菜单选择（个人资料、设置、登出）。
 * Currently only settings navigation and a placeholder logout dialog
 * are implemented.
 * 目前已实现的仅设置导航和占位登出对话框。
 */
const handleUserMenuSelect = (key: string) => {
  if (key === 'settings') router.push('/settings')
  else if (key === 'logout') {
    if (window.$dialog) {
      window.$dialog.info({ title: '提示', content: '退出登录功能开发中' })
    }
  }
}

/**
 * ========================================
 * Watchers / 侦听器
 * ========================================
 */

/**
 * Watch route changes to keep the active navigation key in sync.
 * 监听路由变化以保持活动导航键同步。
 * Using { immediate: true } ensures the nav is highlighted on initial load.
 * 使用 { immediate: true } 确保初始加载时导航已高亮。
 */
watch(() => route.path, (newPath) => {
  activeKey.value = newPath
}, { immediate: true })

/**
 * ========================================
 * Lifecycle Hooks / 生命周期钩子
 * ========================================
 */

/** Register global keyboard shortcut listener on mount / 挂载时注册全局键盘快捷键监听器 */
onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
})

/** Remove global keyboard shortcut listener on unmount to prevent leaks / 卸载时移除全局键盘快捷键监听器以防止泄漏 */
onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<!-- ================================================================
     Styles (SCSS) / 样式
     ================================================================
     All styles are scoped to this component via the `scoped` attribute.
     The design system leverages CSS custom properties (variables) defined
     globally, combined with a gold/amber accent palette.

     所有样式通过 `scoped` 属性限定在此组件内。
     设计系统利用全局定义的 CSS 自定义属性（变量），结合金色/琥珀色强调色调。

     Key Visual Concepts / 核心视觉概念:
       - Glassmorphism: backdrop-filter blur + semi-transparent backgrounds
         毛玻璃效果：backdrop-filter 模糊 + 半透明背景
       - Gradient accents: golden gradients for active states and branding
         渐变强调色：活动状态和品牌标识用的金色渐变
       - Subtle ambient glow: radial gradients in the background layer
         微妙的氛围光：背景层中的径向渐变
       - Smooth transitions: consistent transition timing variables
         平滑过渡：一致的过渡时间变量
-->

<style lang="scss" scoped>
// ============================================================
// Layout Container / 布局容器
// ============================================================
.main-layout {
  min-height: 100vh;
  background: var(--color-bg);
  position: relative;
}

// ============================================================
// Ambient Background / 环境背景层
// ============================================================
// Three radial gradients create a subtle gold-purple-amber glow
// that adds depth to the layout without distracting from content.
// 三个径向渐变营造柔和的金色-紫色-琥珀色光晕，
// 为布局增添层次感而不干扰内容。
.layout-bg {
  position: fixed;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 0%, rgba(194, 164, 116, 0.06) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(155, 135, 245, 0.06) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(245, 158, 11, 0.03) 0%, transparent 60%);
  pointer-events: none;  // Allow clicks to pass through / 允许点击穿透
  z-index: 0;
}

// ============================================================
// Header — Glassmorphism / 头部 — 毛玻璃效果
// ============================================================
// A sticky header with high z-index, frosted glass background,
// and a subtle golden bottom border. The backdrop-filter creates
// the glass effect by blurring content behind the header.
// 固定头部，高 z-index，磨砂玻璃背景，微妙的金色底部边框。
// backdrop-filter 通过模糊头部背后的内容来创建玻璃效果。
.header {
  height: 64px;
  position: sticky !important;
  top: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.85) !important;
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid rgba(194, 164, 116, 0.15) !important;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.04);
  transition: all var(--transition-base);

  // Modifier: adds deeper shadow when the page is scrolled
  // 修饰符：页面滚动时添加更深的阴影（需 JS 配合）
  &.header--scrolled {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  }
}

// Header inner container: horizontal flex layout with max-width constraint
// 头部内部容器：水平弹性布局，最大宽度约束
.header-inner {
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 32px;
  gap: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

// ============================================================
// Logo Section / Logo 区域
// ============================================================
.header-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex-shrink: 0;
  user-select: none;

  .logo-icon {
    width: 38px;
    height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    // Gold gradient icon background / 金色渐变图标背景
    background: linear-gradient(135deg, #d4af37, #b8860b);
    border-radius: 10px;
    color: #fff;
    box-shadow: 0 4px 12px rgba(212, 175, 55, 0.35);
  }

  .logo-text {
    .logo-title {
      margin: 0;
      font-size: 20px;
      font-weight: 800;
      letter-spacing: -0.3px;
    }
  }
}

// ============================================================
// Search Bar / 搜索栏
// ============================================================
.header-search {
  flex-shrink: 0;

  // Override Naive UI input styles with gold accent borders
  // 重写 Naive UI 输入框样式，使用金色强调边框
  :deep(.n-input) {
    --n-border-radius: 20px;
    --n-border: 1px solid rgba(194, 164, 116, 0.15);
    --n-border-hover: 1px solid rgba(194, 164, 116, 0.35);
    --n-border-focus: 1px solid rgba(194, 164, 116, 0.5);
    --n-box-shadow-focus: 0 0 0 3px rgba(194, 164, 116, 0.12);
    transition: all var(--transition-base);

    &:hover { --n-box-shadow: 0 2px 8px rgba(194, 164, 116, 0.12); }
  }
}

// ============================================================
// Navigation Menu / 导航菜单
// ============================================================
.header-nav {
  display: flex;
  align-items: center;
  gap: 2px;
  flex: 1;
  justify-content: center;

  .nav-item {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 500;
    color: var(--color-text-secondary);
    cursor: pointer;
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);
    white-space: nowrap;
    position: relative;  // Anchor for the nav-indicator / 为 nav-indicator 提供定位锚点

    &:hover {
      color: var(--color-text);
      background: var(--color-primary-subtle);
    }

    // Active state: gold gradient background for visual emphasis
    // 活动状态：金色渐变背景带来视觉强调
    &.active {
      color: var(--color-primary-dark);
      background: linear-gradient(135deg, rgba(212, 175, 55, 0.12), rgba(218, 165, 32, 0.08));
      font-weight: 600;
    }

    // Bottom indicator bar for the active nav item
    // 活动导航项的底部指示条
    .nav-indicator {
      position: absolute;
      bottom: -1px;
      left: 50%;
      transform: translateX(-50%);
      width: 20px;
      height: 2px;
      background: linear-gradient(90deg, var(--color-primary-light), var(--color-accent));
      border-radius: 1px;
    }
  }
}

// ============================================================
// Right Actions / 右侧操作区
// ============================================================
.header-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;

  .lang-label {
    font-size: 13px;
    font-weight: 500;
    margin-left: 4px;
  }

  // Shared style for header action buttons
  // 头部操作按钮的共享样式
  :deep(.header-btn) {
    color: var(--color-text-secondary);
    transition: all var(--transition-fast);

    &:hover {
      color: var(--color-text);
      background: var(--color-primary-subtle);
    }
  }

  // User avatar hover effect: golden border glow
  // 用户头像悬停效果：金色边框发光
  :deep(.user-btn:hover .n-avatar) {
    border-color: var(--color-primary-light);
    transform: scale(1.08);
    box-shadow: 0 4px 12px rgba(212, 175, 55, 0.35);
  }

  // User avatar base style with transition for smooth hover animation
  // 用户头像基础样式，带过渡以实现平滑悬停动画
  :deep(.n-avatar) {
    border: 2px solid var(--color-border);
    transition: all var(--transition-base);
    cursor: pointer;
  }
}

// ============================================================
// Breadcrumb Bar / 面包屑导航条
// ============================================================
// Semi-transparent background with backdrop blur for subtle glass effect.
// Only the last breadcrumb item is rendered in full opacity (current page).
// 半透明背景加 backdrop blur 实现细微玻璃效果。
// 仅最后一个面包屑项（当前页面）以全不透明度显示。
.breadcrumb-bar {
  padding: 12px 32px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--color-border-light);

  :deep(.n-breadcrumb) {
    font-size: 13px;
    font-weight: 500;

    .n-breadcrumb-item__link {
      color: var(--color-text-secondary);
      transition: color var(--transition-fast);
      &:hover { color: var(--color-primary-dark); }
    }
    // Last (current page) breadcrumb item: full opacity text
    // 最后一个（当前页面）面包屑项：全不透明度文字
    .n-breadcrumb-item--last .n-breadcrumb-item__link { color: var(--color-text); }
  }
}

// ============================================================
// Main Content / 主内容区域
// ============================================================
.main-content {
  padding: 0;
  min-height: calc(100vh - 64px);  // Full viewport height minus header / 全视口高度减去头部
  background: transparent;
  // Allow the ambient background to show through
  // 让环境背景能够透出

  .content-wrapper {
    width: 100%;
    height: 100%;
  }
}

// ============================================================
// Page Transition Animations / 页面过渡动画
// ============================================================
// Enter: slow cubic-bezier with slight upward movement and scale
// Leave: faster cubic-bezier with slight upward movement
// 进入：慢速 cubic-bezier，轻微上移和缩放
// 离开：快速 cubic-bezier，轻微上移
.fade-slide-enter-active { transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.fade-slide-leave-active { transition: all 0.2s cubic-bezier(0.4, 0, 1, 1); }
.fade-slide-enter-from { opacity: 0; transform: translateY(20px) scale(0.97); }
.fade-slide-leave-to { opacity: 0; transform: translateY(-10px); }

// ============================================================
// Responsive Breakpoints / 响应式断点
// ============================================================

// Tablet / 平板: hide search bar, compact nav items
// 隐藏搜索栏，紧凑导航项
@media (max-width: 1200px) {
  .header-search { display: none; }
  .header-nav .nav-item { padding: 8px 10px; font-size: 12px; gap: 4px; }
}

// Mobile / 手机: minimal padding, hide nav text labels (icons only)
// 最小内边距，隐藏导航文字标签（仅显示图标）
@media (max-width: 768px) {
  .header-inner { padding: 0 16px; gap: 8px; }
  .header-nav { gap: 0; }
  .header-nav .nav-item span { display: none; }
}
</style>
