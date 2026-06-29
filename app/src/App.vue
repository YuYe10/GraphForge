<!-- ============================================================================
  GraphForge — Root Application Component
  GraphForge — 根应用组件
  ============================================================================

  This is the top-level Vue component that serves as the application shell.
  It is responsible for:

    - Scroll Progress Indicator (滚动进度条)
      A fixed-position progress bar at the very top of the viewport,
      reflecting the user's vertical scroll position as a percentage.

    - Theme System (主题系统)
      Supports light and dark modes via Naive UI's darkTheme. The current
      theme is persisted in localStorage and exposed on `window.__graphforgeTheme`
      so that any code (Vue or non-Vue) can read or toggle it. A `.dark` class
      is synchronously applied to `<html>` for global CSS overrides.

    - Naive UI Provider Hierarchy (Naive UI 提供者层级)
      Wraps the app content in the required Naive UI provider components
      (ConfigProvider, MessageProvider, NotificationProvider, DialogProvider)
      with locale-appropriate i18n settings (Chinese or English).

    - Background Particle Animation (背景粒子动画)
      A canvas-based particle system rendered behind the content, creating
      a subtle ambient "floating dust" effect that adapts its opacity and
      color to the theme.

    - Locale Handling (多语言处理)
      Detects the current vue-i18n locale and forwards matching Naive UI
      locale / date-locale objects so that the UI library's internal text
      (e.g., date picker months) respects the user's language preference.
-->

<template>
  <!-- ========================================================================
    Scroll Progress Bar (滚动进度条)
    ========================================================================
    A thin, animated gradient bar fixed to the top of the viewport.
    Its width dynamically represents the current scroll progress (0%–100%).
  -->
  <div class="scroll-progress" :style="{ width: scrollProgress + '%' }"></div>

  <!-- ========================================================================
    Naive UI Provider Hierarchy (Naive UI Provider 层级)
    ========================================================================
    <n-config-provider>   — Applies theme (light/dark) and locale settings
                            (主题/语言环境设置)
    <n-global-style>       — Injects Naive UI's base CSS reset and typography
                            (注入 Naive UI 的基础 CSS 重置与排版样式)
    <n-message-provider>   — Enables $message() toast-style popups
                            (启用 $message() 弹出式消息提示)
    <n-notification-provider> — Enables $notification() notification cards
                                (启用 $notification() 通知卡片)
    <n-dialog-provider>    — Enables $dialog() modal dialogs
                            (启用 $dialog() 模态对话框)
    <AppContent />          — The actual application content (实际应用内容)
  -->
  <n-config-provider :locale="naiveLocale" :date-locale="naiveDateLocale" :theme="naiveTheme">
    <n-global-style />
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <AppContent />
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
// =============================================================================
// GraphForge App — Script Setup
// 根组件脚本设置
// =============================================================================

import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NConfigProvider, NMessageProvider, NNotificationProvider,
  NDialogProvider, NGlobalStyle,
  zhCN, enUS, dateZhCN, dateEnUS,
  darkTheme
} from 'naive-ui'
import AppContent from './components/AppContent.vue'

const { locale } = useI18n()

// =============================================================================
// Theme System (主题系统)
// =============================================================================

/**
 * Reactive theme mode reference.
 * 响应式主题模式引用。
 *
 * Initialized from localStorage so the user's preference persists across
 * sessions. Falls back to 'light' if no saved preference exists.
 *
 * 从 localStorage 初始化以跨会话持久化用户偏好。无保存值时默认 'light'。
 */
const themeMode = ref(localStorage.getItem('graphforge-theme') || 'light')

/**
 * Computed Naive UI theme object.
 * Naive UI 主题对象的计算属性。
 *
 * - `null`            → Light mode (浅色模式)
 * - `darkTheme`       → Dark mode (深色模式)
 */
const naiveTheme = computed(() => themeMode.value === 'dark' ? darkTheme : null)

/**
 * Expose theme system on the global `window` object.
 * 在全局 window 对象上暴露主题系统。
 *
 * This allows non-Vue code (HTML inline scripts, external tools, etc.) to
 * read the current theme or toggle between light and dark without importing
 * Vue internals.
 *
 * 这允许非 Vue 代码（内联 HTML 脚本、外部工具等）无需导入 Vue 内部实现，
 * 即可读取当前主题或在浅色/深色之间切换。
 *
 * Usage / 使用方式:
 *   window.__graphforgeTheme.toggle()
 *   console.log(window.__graphforgeTheme.mode.value)  // 'dark' | 'light'
 */
if (typeof window !== 'undefined') {
  ;(window as any).__graphforgeTheme = {
    mode: themeMode,
    toggle: () => {
      themeMode.value = themeMode.value === 'dark' ? 'light' : 'dark'
      localStorage.setItem('graphforge-theme', themeMode.value)
    }
  }
}

/**
 * Watch for theme changes and toggle the `.dark` class on <html>.
 * 监听主题变化并在 <html> 上切换 `.dark` 类。
 *
 * The `immediate: true` flag ensures the correct class is applied on initial
 * load, preventing a flash of unstyled content (FOUC).
 *
 * `immediate: true` 确保初始加载时就应用正确的类，
 * 防止出现未样式化内容的闪烁 (FOUC)。
 */
watch(themeMode, (mode) => {
  document.documentElement.classList.toggle('dark', mode === 'dark')
}, { immediate: true })

// =============================================================================
// Locale Handling (多语言处理)
// =============================================================================

/**
 * Computed Naive UI locale object based on the current vue-i18n locale.
 * 根据当前 vue-i18n 语言环境计算 Naive UI 的 locale 配置。
 *
 * This ensures Naive UI's built-in text (date picker, data table pagination,
 * etc.) matches the user's selected language.
 *
 * 确保 Naive UI 的内置文本（日期选择器、数据表格分页等）与用户选择的语言一致。
 */
const naiveLocale = computed(() => locale.value === 'zh' ? zhCN : enUS)

/**
 * Computed Naive UI date-locale object (e.g., for DatePicker).
 * Naive UI 日期 locale 的计算属性（如用于 DatePicker）。
 */
const naiveDateLocale = computed(() => locale.value === 'zh' ? dateZhCN : dateEnUS)

// =============================================================================
// Scroll Progress (滚动进度)
// =============================================================================

/**
 * Current scroll progress as a percentage (0–100).
 * 当前滚动进度百分比 (0–100)。
 */
const scrollProgress = ref(0)

/**
 * Scroll event handler reference, stored so it can be cleaned up on unmount.
 * 滚动事件处理函数引用，存储在变量中以便在卸载时移除。
 */
let scrollHandler = () => {}

// =============================================================================
// Background Particle Animation (背景粒子动画)
// =============================================================================

/** Reference to the dynamically created <canvas> element. */
let particlesCanvas: HTMLCanvasElement | null = null

/** ID of the current requestAnimationFrame frame, used for cancellation. */
let particlesAnimationId = 0

// =============================================================================
// Lifecycle Hooks (生命周期钩子)
// =============================================================================

onMounted(() => {
  // --- Scroll Progress Listener ---
  scrollHandler = () => {
    // Calculate scroll depth: how far down the document the user has scrolled,
    // expressed as a percentage of the total scrollable height.
    // 计算滚动深度：用户已滚动的距离占可滚动总高度的百分比。
    const scrollTop = window.scrollY || document.documentElement.scrollTop
    const docHeight = document.documentElement.scrollHeight - window.innerHeight
    scrollProgress.value = docHeight > 0 ? Math.min((scrollTop / docHeight) * 100, 100) : 0
  }
  // Attach with { passive: true } for optimal scroll performance.
  // 使用 { passive: true } 选项以获得最优滚动性能。
  window.addEventListener('scroll', scrollHandler, { passive: true })

  // --- Initialize Background Particles ---
  initParticles()
})

onUnmounted(() => {
  // Cancel the animation loop when the component is destroyed to prevent
  // memory leaks and unnecessary CPU usage.
  // 组件销毁时取消动画循环，防止内存泄漏和不必要的 CPU 消耗。
  if (particlesAnimationId) cancelAnimationFrame(particlesAnimationId)
  // Remove the canvas element from the DOM.
  // 从 DOM 中移除 canvas 元素。
  particlesCanvas?.remove()
})

// =============================================================================
// Particle System Implementation (粒子系统实现)
// =============================================================================

/**
 * Initialize and start the canvas-based background particle system.
 * 初始化并启动基于 Canvas 的背景粒子系统。
 *
 * This creates a full-screen <canvas> element with a fixed, non-interactive
 * backdrop. The particles drift slowly in random directions, fade in and out
 * with a sinusoidal life cycle, and draw connection lines when within close
 * proximity of each other, producing a subtle "constellation" or "stardust"
 * effect. The gold-ish color (#C2A474) complements the GraphForge brand
 * palette.
 *
 * 创建一个全屏、非交互式的 <canvas> 背景。粒子缓慢漂移，以正弦生命周期
 * 淡入淡出，并在相互靠近时绘制连接线，产生微妙的"星空"或"星尘"效果。
 * 金色调 (#C2A474) 与 GraphForge 的品牌色板相呼应。
 */
function initParticles() {
  // --- Create the Canvas Element ---
  particlesCanvas = document.createElement('canvas')
  particlesCanvas.id = 'particles-canvas'
  particlesCanvas.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:0;opacity:0.25;'
  document.body.appendChild(particlesCanvas)

  const ctx = particlesCanvas.getContext('2d')
  if (!ctx) return

  // --- Responsive Resizing (响应式尺寸调整) ---
  const resize = () => {
    if (!particlesCanvas) return
    particlesCanvas.width = window.innerWidth
    particlesCanvas.height = window.innerHeight
  }
  resize()
  window.addEventListener('resize', resize)

  // --- Particle Data Model (粒子数据模型) ---
  interface Particle {
    x: number        // X position (X 坐标)
    y: number        // Y position (Y 坐标)
    vx: number       // X velocity (X 方向速度)
    vy: number       // Y velocity (Y 方向速度)
    size: number     // Radius in pixels (像素半径)
    opacity: number  // Base opacity (基础不透明度)
    life: number     // Current age in frames (当前帧龄)
    maxLife: number  // Maximum lifespan in frames (最大帧寿命)
  }

  const particles: Particle[] = []
  const MAX_PARTICLES = 30  // Balance between visual density and performance
                            // 视觉密度与性能之间的平衡

  /**
   * Create a new particle with randomized initial properties.
   * 创建一个具有随机初始属性的新粒子。
   */
  function createParticle(): Particle {
    return {
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      vx: (Math.random() - 0.5) * 0.3,  // Very slow horizontal drift (缓慢水平漂移)
      vy: (Math.random() - 0.5) * 0.3,  // Very slow vertical drift (缓慢垂直漂移)
      size: Math.random() * 3 + 1,      // Radius: 1–4 px (半径: 1–4 像素)
      opacity: Math.random() * 0.5 + 0.1, // Base opacity: 0.1–0.6
      life: 0,
      maxLife: Math.random() * 300 + 200  // Lifespan: 200–500 frames (寿命: 200–500 帧)
    }
  }

  // Seed the particle array with initial particles.
  // 初始化粒子数组。
  for (let i = 0; i < MAX_PARTICLES; i++) {
    particles.push(createParticle())
  }

  /**
   * Main animation loop (主动画循环).
   *
   * On each frame:
   *   1. Clear the canvas (清空画布)
   *   2. Update each particle's position and age (更新位置与时长)
   *   3. Wrap off-screen particles to the opposite edge (越界回卷)
   *   4. Draw the particle with a sine-wave fade (正弦淡入淡出绘制)
   *   5. Draw inter-particle connection lines (绘制连线)
   *   6. Respawn particles that have exceeded their lifespan (重生过期粒子)
   *   7. Request the next frame (请求下一帧)
   */
  function animate() {
    if (!ctx || !particlesCanvas) return
    ctx.clearRect(0, 0, particlesCanvas.width, particlesCanvas.height)

    // Iterate backwards so we can safely splice if needed.
    // 反向遍历以方便安全地删除元素。
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i]
      p.x += p.vx
      p.y += p.vy
      p.life++

      // --- Edge Wrapping (越界回卷) ---
      // When a particle drifts off-screen, wrap it to the opposite edge
      // so particles never leave the visible area. The 10px buffer prevents
      // harsh disappearance at the exact boundary.
      // 粒子漂出屏幕时从另一侧重新进入。10px 缓冲防止在边界处突兀消失。
      if (p.x < -10) p.x = window.innerWidth + 10
      if (p.x > window.innerWidth + 10) p.x = -10
      if (p.y < -10) p.y = window.innerHeight + 10
      if (p.y > window.innerHeight + 10) p.y = -10

      // --- Fade Calculation (透明度计算) ---
      // Use a sine curve over the particle's life for a smooth,
      // natural-feeling fade-in and fade-out.
      // 使用正弦曲线模拟自然平滑的淡入淡出效果。
      const fadeRatio = Math.sin((p.life / p.maxLife) * Math.PI)
      const alpha = p.opacity * fadeRatio

      // --- Draw Particle (绘制粒子) ---
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
      // Gold hue matching the GraphForge brand identity.
      // 金色调，与 GraphForge 品牌形象保持一致。
      ctx.fillStyle = `rgba(194, 164, 116, ${alpha})`
      ctx.fill()

      // --- Draw Inter-Particle Connections (绘制粒子间连线) ---
      // If two particles are close enough (within 150px), draw a subtle
      // line between them. The line's opacity decreases with distance,
      // creating a smooth fade. This produces a "molecular" or
      // "constellation" visual effect.
      // 若两个粒子距离小于 150px，在它们之间画一条细线。
      // 线条透明度随距离递减，形成平滑过渡，产生"分子"或"星座"效果。
      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j]
        const dx = p.x - p2.x
        const dy = p.y - p2.y
        const dist = Math.sqrt(dx * dx + dy * dy)

        if (dist < 150) {
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(p2.x, p2.y)
          // Line opacity: 0.06 at dist=0 → 0 at dist=150
          // 线条不透明度：dist=0 时为 0.06，dist=150 时为 0
          ctx.strokeStyle = `rgba(194, 164, 116, ${0.06 * (1 - dist / 150)})`
          ctx.lineWidth = 0.5
          ctx.stroke()
        }
      }

      // --- Respawn Expired Particles (重生过期粒子) ---
      // When a particle reaches its maxLife, replace it with a fresh one
      // to keep the particle count constant.
      // 粒子达到最大寿命时替换为新粒子，保持粒子总数恒定。
      if (p.life >= p.maxLife) {
        particles[i] = createParticle()
      }
    }

    // Schedule next frame (调度下一帧)
    particlesAnimationId = requestAnimationFrame(animate)
  }

  // Start the animation loop (启动动画循环)
  animate()
}
</script>

<!-- =========================================================================
  GraphForge App — Global Styles
  全局样式
  =========================================================================

  This <style lang="scss"> block defines global styles scoped to the #app
  root element. It includes:

    - Scroll Progress Bar (滚动进度条) — Fixed top bar with gradient fill
    - Dark Mode Overrides (深色模式覆盖) — Theme variables for html.dark
    - Naive UI Component Theming (组件主题定制) — Card, Button, Input, Tag,
      Data Table, Modal, Tabs, Collapse, and more — all styled with a
      luxurious gold-accented design language
    - Transition Animations (过渡动画) — fade-slide helpers for page transitions
-->

<style lang="scss">
// =============================================================================
// GraphForge App — Global Component Styles
// International Design Excellence — 国际化卓越设计
// =============================================================================

// --- Scroll Progress Bar (滚动进度条) ---
// A thin fixed bar at the very top of the viewport indicating scroll position.
// Uses a multi-stop gradient with a smooth animation for a premium feel.
//
// 固定在视口顶部的一条细进度条，使用多段渐变动画呈现出高级质感。
.scroll-progress {
  position: fixed;
  top: 0;
  left: 0;
  height: 2.5px;
  background: linear-gradient(90deg, var(--color-primary-light), var(--color-accent), #f59e0b, #10b981);
  background-size: 300% 100%;
  animation: gradientFlow 4s linear infinite;
  z-index: 10000;
  transition: width 0.15s linear;
  border-radius: 0 2px 2px 0;
  box-shadow: 0 0 8px rgba(194, 164, 116, 0.4);
}

// --- Ripple Effect Keyframes (水波纹动画关键帧) ---
// Used by the v-ripple custom directive.
// 由 v-ripple 自定义指令使用。
@keyframes ripple-effect {
  to {
    transform: scale(1);
    opacity: 0;
  }
}

// =============================================================================
// Dark Mode Theme Variables (深色模式主题变量)
// =============================================================================
// Applied when the `.dark` class is present on <html>.
// 当 <html> 元素包含 `.dark` 类时生效。
html.dark {
  #app {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    color: #e2e8f0;
  }

  // Dark-mode card adjustments (深色模式卡片适配)
  :deep(.n-card) {
    background: rgba(30, 41, 59, 0.8) !important;
    border-color: rgba(71, 85, 105, 0.3) !important;
  }

  :deep(.n-layout) { background: transparent !important; }
  :deep(.n-layout-header) { background: rgba(15, 23, 42, 0.9) !important; }
}

// =============================================================================
// Base Reset (基础重置)
// =============================================================================
* { margin: 0; padding: 0; box-sizing: border-box; }

#app {
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
}

// =============================================================================
// Naive UI — Global Card Theming (全局卡片主题)
// =============================================================================
:deep(.n-card) {
  border-radius: var(--radius-xl) !important;
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border-light);

  // Hover elevation effect (悬停时升起效果)
  &.n-card--hoverable:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg), 0 0 30px var(--color-primary-glow);
  }

  > .n-card-header {
    font-weight: 700;
    font-size: 17px;
    padding: 20px 24px 16px;
    border-bottom: 1px solid var(--color-border-light);
    letter-spacing: -0.2px;
  }

  > .n-card__content {
    padding: 24px;
  }

  > .n-card__footer {
    padding: 16px 24px;
    border-top: 1px solid var(--color-border-light);
  }
}

// =============================================================================
// Naive UI — Global Button Theming (全局按钮主题)
// Luxurious Gold Design Language — 奢华金色设计语言
// =============================================================================
:deep(.n-button) {
  border-radius: var(--radius-md) !important;
  font-weight: 600 !important;
  letter-spacing: 0.2px;
  transition: all var(--transition-base) !important;

  &:focus { outline: none !important; }

  // --- Primary Button — Gold Gradient (主按钮 — 金色渐变) ---
  &.n-button--primary-type {
    background: linear-gradient(135deg, #d4af37, #b8860b) !important;
    border: none !important;
    color: #fff !important;
    box-shadow: 0 2px 8px rgba(212, 175, 55, 0.3);

    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #c9a668, #9a7509) !important;
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(212, 175, 55, 0.45);
    }

    &:active:not(:disabled) {
      background: linear-gradient(135deg, #b8860b, #8b6914) !important;
      transform: translateY(0);
    }

    &:focus:not(:disabled) {
      box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.3);
    }
  }

  // --- Default Button (默认按钮) ---
  &.n-button--default-type {
    background: var(--color-surface);
    border: 1px solid #e0e0e0 !important;
    color: var(--color-text-secondary);

    &:hover:not(:disabled) {
      background: var(--color-surface-alt);
      border-color: var(--color-primary-light) !important;
      color: var(--color-primary-dark);
      transform: translateY(-2px);
    }

    &:focus:not(:disabled) {
      border-color: var(--color-primary-light) !important;
      box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.15);
    }
  }

  // --- Success Button (成功按钮) ---
  &.n-button--success-type {
    background: linear-gradient(135deg, #10b981, #059669) !important;
    border: none !important;
    color: #fff !important;
    box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);

    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #34d399, #10b981) !important;
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(16, 185, 129, 0.45);
    }
  }

  // --- Warning Button (警告按钮) ---
  &.n-button--warning-type {
    background: linear-gradient(135deg, #f59e0b, #d97706) !important;
    border: none !important;
    color: #fff !important;

    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #fbbf24, #f59e0b) !important;
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(245, 158, 11, 0.45);
    }
  }

  // --- Error Button (错误按钮) ---
  &.n-button--error-type {
    background: linear-gradient(135deg, #ef4444, #dc2626) !important;
    border: none !important;
    color: #fff !important;

    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #f87171, #ef4444) !important;
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(239, 68, 68, 0.45);
    }
  }

  // --- Text Buttons (文本按钮) ---
  &.n-button--text-type {
    border: none !important;
    background: transparent;

    &.n-button--primary-type {
      color: var(--color-primary-light);
      &:hover:not(:disabled) { background: var(--color-primary-subtle) !important; color: var(--color-primary-dark); }
    }
    &.n-button--error-type {
      color: var(--color-error);
      &:hover:not(:disabled) { background: rgba(239, 68, 68, 0.1) !important; }
    }
  }

  // --- Ghost Button (幽灵按钮) ---
  &.n-button--ghost-type {
    border-color: var(--color-primary-light) !important;
    color: var(--color-primary-light);
    &:hover:not(:disabled) {
      background: var(--color-primary-subtle) !important;
      border-color: var(--color-primary-dark) !important;
    }
  }
}

// =============================================================================
// Naive UI — Global Input / Select Theming (全局输入框/选择器主题)
// =============================================================================
:deep(.n-input),
:deep(.n-input-number),
:deep(.n-select) {
  .n-input__border,
  .n-input__state-border,
  .n-base-selection {
    border-radius: var(--radius-md) !important;
  }
}

:deep(.n-input) {
  textarea {
    font-family: var(--font-mono);
    font-size: 14px;
    line-height: 1.7;
  }
}

// =============================================================================
// Naive UI — Global Tag Theming (全局标签主题)
// =============================================================================
:deep(.n-tag) {
  font-weight: 600;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  letter-spacing: 0.2px;
  transition: all var(--transition-fast);

  &.n-tag--round { border-radius: 16px; }

  &:hover { transform: scale(1.05); }
}

// =============================================================================
// Naive UI — Global Alert Theming (全局提示框主题)
// =============================================================================
:deep(.n-alert) {
  border-radius: var(--radius-lg);
  border-left-width: 4px;
  font-weight: 500;
}

// =============================================================================
// Naive UI — Global Data Table Theming (全局数据表格主题)
// =============================================================================
:deep(.n-data-table) {
  border-radius: var(--radius-xl);
  overflow: hidden;

  .n-data-table-th {
    background: linear-gradient(135deg, rgba(194, 164, 116, 0.06), rgba(155, 135, 245, 0.04));
    font-weight: 700;
    font-size: 13px;
    color: var(--color-text);
    letter-spacing: 0.3px;
    text-transform: uppercase;
  }

  .n-data-table-td {
    padding: 14px 16px;
    font-size: 14px;
  }

  .n-data-table-tr {
    transition: background var(--transition-fast);

    &:hover .n-data-table-td {
      background: rgba(194, 164, 116, 0.04);
    }
  }
}

// =============================================================================
// Naive UI — Global Progress Bar Theming (全局进度条主题)
// =============================================================================
:deep(.n-progress) {
  .n-progress-graph-line-fill {
    background: linear-gradient(90deg, var(--color-primary-light), var(--color-accent), var(--color-primary-dark));
    background-size: 200% 100%;
    animation: gradientFlow 3s ease infinite;
  }
}

// =============================================================================
// Naive UI — Global Modal & Drawer Theming (全局模态框和抽屉主题)
// =============================================================================
:deep(.n-modal) {
  .n-dialog {
    border-radius: var(--radius-2xl) !important;
    overflow: hidden;
  }
  .n-dialog__title {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.3px;
  }
}

:deep(.n-drawer) {
  .n-drawer-header {
    font-weight: 700;
    font-size: 18px;
    letter-spacing: -0.2px;
    border-bottom: 1px solid var(--color-border-light);
  }
}

// =============================================================================
// Naive UI — Global Spin / Loading Theming (全局加载动画主题)
// =============================================================================
:deep(.n-spin) {
  .n-spin-description {
    margin-top: 12px;
    font-weight: 600;
    color: var(--color-text-secondary);
  }
}

// =============================================================================
// Naive UI — Global Tabs Theming (全局标签页主题)
// =============================================================================
:deep(.n-tabs) {
  .n-tabs-nav {
    border-radius: var(--radius-lg);
    padding: 4px;
  }

  .n-tabs-tab {
    font-weight: 600;
    border-radius: var(--radius-md);
    transition: all var(--transition-base);

    &.n-tabs-tab--active {
      background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(248,250,252,0.8));
      box-shadow: var(--shadow-sm);
    }
  }
}

// =============================================================================
// Naive UI — Global Collapse Theming (全局折叠面板主题)
// =============================================================================
:deep(.n-collapse) {
  border-radius: var(--radius-lg);
  overflow: hidden;

  .n-collapse-item__header {
    font-weight: 600;
    transition: all var(--transition-fast);
  }
}

// =============================================================================
// Naive UI — Global Divider Theming (全局分割线主题)
// =============================================================================
:deep(.n-divider) {
  .n-divider__line {
    background: var(--color-border-light);
  }
}

// =============================================================================
// Naive UI — Notification Animation (通知动画)
// =============================================================================
:deep(.n-notification) {
  border-radius: var(--radius-lg) !important;
  box-shadow: var(--shadow-lg) !important;
  animation: slideInUp 0.4s ease-out !important;
}

// =============================================================================
// Transition Animations (过渡动画)
// =============================================================================
// fade-slide — Used by Vue <Transition> for route / component enter/leave
// 用于 Vue <Transition> 的路由/组件进入/离开动画
.fade-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.fade-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 1, 1);
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(16px) scale(0.98);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-12px) scale(0.98);
}

// =============================================================================
// Global Link Styles (全局链接样式)
// =============================================================================
a {
  color: var(--color-primary-dark);
  text-decoration: none;
  transition: color var(--transition-fast);
  &:hover { color: var(--color-primary-light); }
}
</style>
