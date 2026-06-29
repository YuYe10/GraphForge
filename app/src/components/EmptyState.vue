<!--
  ============================================================================
  EmptyState.vue — Empty State Placeholder / 空状态占位组件
  ============================================================================
  Role:
    Renders a visually appealing empty-state placeholder that is shown when a
    page or section has no data to display. It features:
      - An animated geometric illustration (circles, diamond, square) that
        floats with CSS keyframe animations.
      - A central icon whose type/color is driven by the `type` prop.
      - A title, optional description, and optional action button/slot.

    This component eliminates the need for static image assets and provides
    a cohesive visual language for all "no data" scenarios across the app.

    当页面或区域没有数据可显示时，呈现一个视觉上吸引人的空状态占位组件。它具有：
      - 动态几何图形插图（圆形、菱形、正方形），使用 CSS 关键帧动画浮动。
      - 中央图标，其类型/颜色由 `type` prop 驱动。
      - 标题、可选描述和可选操作按钮/插槽。

    该组件消除了对静态图片资源的需求，为应用中所有"无数据"场景提供了
    统一的视觉语言。

  Design / 设计要点:
    - 8 context types each map to a distinct icon and color.
    - The default slot can replace the built-in button for custom actions.
    - Geometric shapes use `opacity: 0.12` for subtlety and independent
      float animations for a lively but non-distracting effect.
    - All animations respect the `prefers-reduced-motion` pattern in spirit
      (they are purely decorative).
    ========================================================================
-->

<template>
  <div class="empty-state-wrapper">
    <!--
      Animated geometric illustration / 动态几何插图
      The `illustration-${type}` class allows per-type overrides if needed.
      Five abstract shapes float independently in the background.
      `illustration-${type}` 类允许在需要时按类型覆盖。
      五个抽象形状在背景中独立浮动。
    -->
    <div class="empty-illustration" :class="`illustration-${type}`">
      <!-- Large circle / 大圆形 -->
      <div class="geo-circle geo-1"></div>
      <!-- Medium circle / 中圆形 -->
      <div class="geo-circle geo-2"></div>
      <!-- Small circle / 小圆形 -->
      <div class="geo-circle geo-3"></div>
      <!-- Rotated diamond / 旋转菱形 -->
      <div class="geo-diamond geo-4"></div>
      <!-- Square / 方形 -->
      <div class="geo-square geo-5"></div>

      <!--
        Central icon on a frosted-glass circular background.
        中央图标，位于毛玻璃圆形背景上。
      -->
      <div class="empty-icon">
        <n-icon :size="iconSize" :color="iconColor">
          <component :is="icon" />
        </n-icon>
      </div>
    </div>

    <!-- Title / 标题 -->
    <h3 class="empty-title">{{ title }}</h3>

    <!--
      Description paragraph (only rendered when non-empty).
      描述段落（仅在非空时渲染）。
    -->
    <p v-if="description" class="empty-description">{{ description }}</p>

    <!--
      Actions area / 操作区域
      - Uses the default slot so consumers can inject custom content.
      - Falls back to an <n-button> when `actionLabel` is provided.
      - Uses the default slot 以便使用者注入自定义内容。
      - 当提供 `actionLabel` 时，回退到 <n-button>。
    -->
    <div v-if="$slots.default || actionLabel" class="empty-actions">
      <slot>
        <n-button v-if="actionLabel" type="primary" @click="$emit('action')" size="large" secondary>
          <template v-if="actionIcon" #icon>
            <n-icon><component :is="actionIcon" /></n-icon>
          </template>
          {{ actionLabel }}
        </n-button>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * ============================================================================
 * EmptyState — Script
 * ============================================================================
 *
 * Provides the type-driven icon and color mappings, and computes the active
 * icon/color from the `type` prop.
 *
 * 提供由类型驱动的图标和颜色映射，并根据 `type` prop 计算当前图标/颜色。
 */

import { computed } from 'vue'
import { NIcon, NButton } from 'naive-ui'
import {
  DocumentTextOutline, CubeOutline, SearchOutline,
  CloudUploadOutline, GitNetworkOutline, ChatbubbleOutline,
  ServerOutline, FolderOpenOutline
} from '@vicons/ionicons5'

/**
 * @typedef {'document'|'data'|'search'|'upload'|'graph'|'chat'|'server'|'folder'} EmptyStateType
 * Determines which icon and accent color are shown.
 * 决定显示哪个图标和强调色。
 */

/**
 * Props / 属性
 * @property {EmptyStateType} [type='data']         - Context type driving icon/color / 驱动图标/颜色的上下文类型
 * @property {string}         [title='暂无数据']      - Primary heading / 主标题
 * @property {string}         [description='']        - Secondary text (optional) / 辅助文本（可选）
 * @property {string}         [actionLabel='']         - Text for the default action button / 默认操作按钮的文本
 * @property {any}            [actionIcon]             - Ionicon5 icon for the action button / 操作按钮的 Ionicon5 图标
 * @property {number}         [iconSize=48]            - Size (px) of the central icon / 中央图标的大小（像素）
 */
const props = withDefaults(defineProps<{
  type?: 'document' | 'data' | 'search' | 'upload' | 'graph' | 'chat' | 'server' | 'folder'
  title?: string
  description?: string
  actionLabel?: string
  actionIcon?: any
  iconSize?: number
}>(), {
  type: 'data',
  title: '暂无数据',
  description: '',
  actionLabel: '',
  iconSize: 48
})

/**
 * Emits / 事件
 * - 'action': Fired when the default action button is clicked / 默认操作按钮点击时触发
 */
defineEmits<{ action: [] }>()

// ---------------------------------------------------------------------------
// Icon mapping / 图标映射
// Maps each EmptyStateType to its corresponding Ionicon5 component.
// 将每个 EmptyStateType 映射到对应的 Ionicon5 组件。
// ---------------------------------------------------------------------------
const iconMap: Record<string, any> = {
  document: DocumentTextOutline,
  data: CubeOutline,
  search: SearchOutline,
  upload: CloudUploadOutline,
  graph: GitNetworkOutline,
  chat: ChatbubbleOutline,
  server: ServerOutline,
  folder: FolderOpenOutline
}

/**
 * Resolved icon component based on the current `type` prop.
 * Falls back to `data` (CubeOutline) for unknown types.
 * 根据当前 `type` prop 解析的图标组件。未知类型回退到 `data`（CubeOutline）。
 */
const icon = computed(() => iconMap[props.type] || iconMap.data)

// ---------------------------------------------------------------------------
// Color mapping / 颜色映射
// Each type gets a distinctive accent color for the central icon.
// 每种类型都有一个独特的强调色用于中央图标。
// ---------------------------------------------------------------------------
const colorMap: Record<string, string> = {
  document: '#d4af37',
  data: '#9b87f5',
  search: '#3b82f6',
  upload: '#10b981',
  graph: '#f59e0b',
  chat: '#8b5cf6',
  server: '#6366f1',
  folder: '#c2a474'
}

/**
 * Resolved icon color based on the current `type` prop.
 * Falls back to purple (`#9b87f5`) for unknown types.
 * 根据当前 `type` prop 解析的图标颜色。未知类型回退到紫色（`#9b87f5`）。
 */
const iconColor = computed(() => colorMap[props.type] || '#9b87f5')
</script>

<style lang="scss" scoped>
// ==========================================================================
// Empty State Styles / 空状态样式
// ==========================================================================

// --------------------------------------------------------------------------
// Wrapper / 外层容器
// --------------------------------------------------------------------------
.empty-state-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  animation: fadeInUp 0.6s ease-out both;
}

// --------------------------------------------------------------------------
// Animated geometric illustration container / 动态几何插图容器
// --------------------------------------------------------------------------
.empty-illustration {
  position: relative;
  width: 140px;
  height: 140px;
  margin-bottom: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

// --------------------------------------------------------------------------
// Geometric shapes (abstract decorative elements) / 几何形状（抽象装饰元素）
// All positioned absolutely within the parent, with low opacity for subtlety.
// 所有元素在父容器内绝对定位，低透明度以保持柔和。
// --------------------------------------------------------------------------
[class*="geo-"] {
  position: absolute;
  opacity: 0.12;
  transition: all 0.6s ease;
}

.geo-circle {
  border-radius: 50%;
}

// Large floating circle / 大浮动圆形
.geo-1 {
  width: 100px; height: 100px;
  background: var(--color-primary-light, #c2a474);
  animation: geoFloat1 4s ease-in-out infinite;
  top: 10px; left: 20px;
}

// Medium floating circle / 中浮动圆形
.geo-2 {
  width: 60px; height: 60px;
  background: var(--color-accent, #9b87f5);
  animation: geoFloat2 5s ease-in-out infinite;
  top: 50px; right: 10px;
}

// Small floating circle / 小浮动圆形
.geo-3 {
  width: 40px; height: 40px;
  background: #f59e0b;
  animation: geoFloat3 3.5s ease-in-out infinite;
  bottom: 5px; left: 15px;
}

// Rotated diamond shape / 旋转菱形
.geo-diamond {
  width: 30px; height: 30px;
  background: #10b981;
  transform: rotate(45deg);
  animation: geoFloat1 4.5s ease-in-out infinite reverse;
  top: 0; right: 30px;
  border-radius: 4px;
}

// Square shape / 方形
.geo-square {
  width: 24px; height: 24px;
  background: #3b82f6;
  animation: geoFloat2 3.8s ease-in-out infinite reverse;
  bottom: 20px; right: 20px;
  border-radius: 4px;
}

// --------------------------------------------------------------------------
// Central icon with frosted-glass background / 带毛玻璃背景的中央图标
// --------------------------------------------------------------------------
.empty-icon {
  position: relative;
  z-index: 2;
  width: 72px; height: 72px;
  border-radius: 50%;
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 8px 32px rgba(0,0,0,0.08),
    inset 0 1px 0 rgba(255,255,255,0.8);
}

// --------------------------------------------------------------------------
// Text elements / 文本元素
// --------------------------------------------------------------------------
.empty-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 8px;
  letter-spacing: -0.2px;
}

.empty-description {
  font-size: 14px;
  color: var(--color-text-muted);
  margin: 0 0 24px;
  max-width: 360px;
  line-height: 1.5;
}

// Actions area with staggered fade-in / 带错位淡入效果的操作区域
.empty-actions {
  animation: fadeInUp 0.6s ease-out 0.2s both;
}

// --------------------------------------------------------------------------
// Keyframe animations for geometric floating / 几何形状浮动关键帧动画
// Each shape has a unique duration/easing combination for organic feel.
// 每个形状都有独特的时长/缓动组合，营造有机感。
// --------------------------------------------------------------------------

// Float pattern A — multi-stop translation + scale / 浮动模式 A — 多段位移 + 缩放
@keyframes geoFloat1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(6px, -8px) scale(1.05); }
  66% { transform: translate(-4px, 4px) scale(0.95); }
}

// Float pattern B — two-stop translation + scale / 浮动模式 B — 两段位移 + 缩放
@keyframes geoFloat2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-8px, 6px) scale(1.08); }
}

// Float pattern C — faster, more pronounced bounce / 浮动模式 C — 更快、更明显的弹跳
@keyframes geoFloat3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(8px, -4px) scale(1.1); }
}
</style>
