<!--
  ============================================================================
  CommandPalette.vue — Command Palette / 命令面板
  ============================================================================
  Role:
    Provides a VS Code-style command palette that overlays the entire screen.
    Users can search for commands by typing, navigate the result list with
    keyboard arrows, and execute commands to navigate pages or trigger actions.
    Displays golden-accented UI with icon badges and keyboard shortcut hints.

    提供类似 VS Code 风格的命令面板，覆盖整个屏幕。用户可通过输入搜索命令、
    使用键盘方向键导航结果列表，并执行命令来导航页面或触发操作。
    显示金色强调的 UI，带有图标徽章和键盘快捷键提示。

  Design / 设计要点:
    - Teleported to <body> to ensure highest stacking context.
    - Fuzzy search across label, description, and key.
    - Keyboard-first interaction: arrows, Enter, Escape.
    - Scrolls the active item into view automatically.
    - Transition animations for overlay and dialog.
    ========================================================================
-->

<template>
  <!--
    Teleport to body / 传送到 body 元素
    Ensures the palette overlays above all other content regardless of DOM depth.
    确保面板覆盖在所有其他内容之上，不受 DOM 层级影响。
  -->
  <teleport to="body">
    <!--
      Transition wrapper for enter/leave animations / 进入/离开动画过渡
      The "palette" name maps to CSS transition classes defined below.
      "palette" 名称映射到下方定义的 CSS 过渡类。
    -->
    <transition name="palette">
      <!--
        Overlay backdrop / 遮罩层背景
        - v-if controls visibility (bound to `visible` prop)
        - @click.self closes the palette when clicking outside the dialog
        - v-if 控制可见性（绑定到 `visible` prop）
        - @click.self 在点击对话框外部时关闭面板
      -->
      <div v-if="visible" class="palette-overlay" @click.self="close">
        <div class="palette-dialog" @click.stop>
          <!--
            Search input row / 搜索输入行
            Contains the search icon, text input, and ESC badge.
            包含搜索图标、文本输入框和 ESC 徽章。
          -->
          <div class="palette-input-wrap">
            <n-icon size="20" color="#c2a474"><search-outline /></n-icon>
            <input
              ref="inputRef"
              v-model="query"
              class="palette-input"
              placeholder="输入命令搜索..."
              @keydown="handleKeydown"
              autofocus
            />
            <kbd class="palette-kbd">ESC</kbd>
          </div>

          <!--
            Results list / 结果列表
            Displays filtered commands or an empty-state message.
            显示过滤后的命令或空状态消息。
          -->
          <div class="palette-results">
            <template v-if="filteredCommands.length > 0">
              <div
                v-for="(cmd, idx) in filteredCommands"
                :key="cmd.key"
                /**
                 * Dynamic template ref: captures the DOM element of the active
                 * item so we can scroll it into view when activeIndex changes.
                 * 动态模板引用：捕获当前激活项的 DOM 元素，以便在 activeIndex
                 * 变化时将其滚动到可视区域。
                 */
                :ref="(el: any) => { if (idx === activeIndex) activeEl = el }"
                :class="['palette-item', { active: idx === activeIndex }]"
                @click="execute(cmd)"
                /**
                 * mousemove updates activeIndex so the keyboard highlight
                 * follows the cursor, and vice versa.
                 * mousemove 更新 activeIndex，使键盘高亮跟随鼠标，反之亦然。
                 */
                @mousemove="activeIndex = idx"
              >
                <!-- Command icon with golden gradient background -->
                <div class="palette-item-icon" :style="{ background: cmd.bg }">
                  <n-icon size="16"><component :is="cmd.icon" /></n-icon>
                </div>
                <div class="palette-item-content">
                  <span class="palette-item-label">{{ cmd.label }}</span>
                  <span class="palette-item-desc">{{ cmd.desc }}</span>
                </div>
                <!-- Keyboard shortcut display (e.g., ["G","D"]) -->
                <div class="palette-item-shortcut" v-if="cmd.shortcut">
                  <kbd v-for="k in cmd.shortcut" :key="k">{{ k }}</kbd>
                </div>
              </div>
            </template>
            <!-- Empty state when no commands match the query -->
            <div v-else class="palette-empty">
              <span>未找到匹配的命令</span>
            </div>
          </div>

          <!--
            Footer with keyboard hints / 带有键盘提示的底部栏
            Reminds users of available navigation keys.
            提醒用户可用的导航键。
          -->
          <div class="palette-footer">
            <div class="palette-hints">
              <span><kbd>↑↓</kbd> 导航</span>
              <span><kbd>↵</kbd> 选择</span>
              <span><kbd>ESC</kbd> 关闭</span>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
/**
 * ============================================================================
 * CommandPalette — Script
 * ============================================================================
 *
 * Manages the command list, search/filter, keyboard navigation, and action
 * execution for the command palette overlay.
 *
 * 管理命令面板覆盖层的命令列表、搜索/过滤、键盘导航和操作执行。
 */

import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  SearchOutline, GridOutline, CloudUploadOutline,
  DocumentTextOutline, OptionsOutline, GitNetworkOutline,
  CodeSlashOutline, TimeOutline, SettingsOutline,
  ChatbubbleEllipsesOutline, RefreshOutline
} from '@vicons/ionicons5'

const router = useRouter()

/**
 * @typedef {Object} Command
 * @property {string}   key       - Unique identifier used as :key in v-for loops
 *                                   唯一标识符，用作 v-for 循环的 :key
 * @property {string}   label     - Display label (Chinese) / 显示标签（中文）
 * @property {string}   desc      - Description / 描述
 * @property {any}      icon      - Ionicon5 component reference / Ionicon5 组件引用
 * @property {string}   bg        - CSS gradient background for the icon badge
 *                                   图标徽章的 CSS 渐变背景
 * @property {string[]} [shortcut] - Optional keyboard shortcut keys (e.g., ["G","D"])
 *                                   可选键盘快捷键（例如 ["G","D"]）
 * @property {() => void} action  - Function to execute when the command is selected
 *                                   选中命令时执行的函数
 */
interface Command {
  key: string
  label: string
  desc: string
  icon: any
  bg: string
  shortcut?: string[]
  action: () => void
}

/**
 * Props / 属性
 * @property {boolean} visible - Whether the command palette is shown / 是否显示命令面板
 */
const props = defineProps<{ visible: boolean }>()

/**
 * Emits / 事件
 * - 'update:visible': Emitted when the palette should be shown/hidden (v-model support)
 *                     当面板应显示/隐藏时触发（支持 v-model）
 */
const emit = defineEmits<{ 'update:visible': [boolean] }>()

// ---------------------------------------------------------------------------
// Reactive state / 响应式状态
// ---------------------------------------------------------------------------

/** Current search query string / 当前搜索查询字符串 */
const query = ref('')

/** Index of the currently highlighted command in the filtered list / 当前高亮命令在过滤列表中的索引 */
const activeIndex = ref(0)

/** Template ref to the <input> element for auto-focus / <input> 元素的模板引用，用于自动聚焦 */
const inputRef = ref<HTMLInputElement>()

/** Template ref to the currently active <div> for scroll-into-view / 当前激活 <div> 的模板引用，用于滚动到可视区域 */
const activeEl = ref<HTMLElement>()

// ---------------------------------------------------------------------------
// Command definitions / 命令定义
// ---------------------------------------------------------------------------

/**
 * All available commands in the palette.
 * Each entry maps to a route, a global action, or a page reload.
 * Shortcuts are displayed as hints; actual browser keybindings may be
 * configured separately.
 *
 * 面板中所有可用命令。每个条目映射到一个路由、全局操作或页面刷新。
 * 快捷键显示为提示；实际的浏览器按键绑定可单独配置。
 */
const commands: Command[] = [
  { key: 'dashboard',   label: '仪表盘',     desc: '查看知识图谱全景',              icon: GridOutline,                bg: 'linear-gradient(135deg,#d4af37,#b8860b)',  shortcut: ['G','D'], action: () => router.push('/') },
  { key: 'upload',      label: '知识构建',   desc: '上传文档构建知识',              icon: CloudUploadOutline,         bg: 'linear-gradient(135deg,#c9a668,#9a7509)',  shortcut: ['G','U'], action: () => router.push('/knowledge') },
  { key: 'documents',   label: '文档管理',   desc: '查看已上传文档',                icon: DocumentTextOutline,        bg: 'linear-gradient(135deg,#3b82f6,#1e40af)',  shortcut: ['G','M'], action: () => router.push('/documents') },
  { key: 'cards',       label: '知识卡片',   desc: '管理知识卡片',                  icon: OptionsOutline,             bg: 'linear-gradient(135deg,#9b87f5,#7c6ae0)',  shortcut: ['G','K'], action: () => router.push('/knowledge-card') },
  { key: 'graph',       label: '图谱可视化', desc: '交互式知识图谱',                icon: GitNetworkOutline,          bg: 'linear-gradient(135deg,#10b981,#059669)',  shortcut: ['G','G'], action: () => router.push('/graph') },
  { key: 'query',       label: '知识查询',   desc: 'Cypher 查询图谱',               icon: CodeSlashOutline,           bg: 'linear-gradient(135deg,#3b82f6,#2563eb)',  shortcut: ['G','Q'], action: () => router.push('/query') },
  { key: 'status',      label: '处理状态',   desc: '查看任务进度',                  icon: TimeOutline,                bg: 'linear-gradient(135deg,#f59e0b,#d97706)',  shortcut: ['G','S'], action: () => router.push('/status') },
  { key: 'settings',    label: '系统设置',   desc: '配置 AI 与数据库',              icon: SettingsOutline,            bg: 'linear-gradient(135deg,#8b5cf6,#6d28d9)',  action: () => router.push('/settings') },
  { key: 'qa',          label: '智能问答',   desc: '向知识图谱提问',                icon: ChatbubbleEllipsesOutline,  bg: 'linear-gradient(135deg,#ec4899,#db2777)',  action: () => { (window as any).__openQA?.(); close() } },
  { key: 'refresh',     label: '刷新当前页面', desc: '重新加载数据',                icon: RefreshOutline,             bg: 'linear-gradient(135deg,#64748b,#475569)',  shortcut: ['Ctrl','R'], action: () => window.location.reload() },
]

// ---------------------------------------------------------------------------
// Computed / 计算属性
// ---------------------------------------------------------------------------

/**
 * Filters the command list based on the current search query.
 * Performs a case-insensitive match against label, description, and key.
 * Returns the full list when the query is empty.
 *
 * 根据当前搜索查询过滤命令列表。对标签、描述和键执行不区分大小写的匹配。
 * 当查询为空时返回完整列表。
 */
const filteredCommands = computed(() => {
  if (!query.value.trim()) return commands
  const q = query.value.toLowerCase()
  return commands.filter(c =>
    c.label.toLowerCase().includes(q) ||
    c.desc.toLowerCase().includes(q) ||
    c.key.toLowerCase().includes(q)
  )
})

// ---------------------------------------------------------------------------
// Methods / 方法
// ---------------------------------------------------------------------------

/**
 * Closes the palette, resets the search query, and resets the active index.
 * 关闭面板，重置搜索查询，并重置活动索引。
 */
function close() {
  emit('update:visible', false)
  query.value = ''
  activeIndex.value = 0
}

/**
 * Executes a command's action and closes the palette.
 * @param {Command} cmd - The command to execute / 要执行的命令
 */
function execute(cmd: Command) {
  cmd.action()
  close()
}

/**
 * Handles keyboard events on the search input.
 * Supports arrow navigation, Enter to select, and Escape to close.
 *
 * 处理搜索输入框上的键盘事件。
 * 支持方向键导航、Enter 选择、Escape 关闭。
 *
 * @param {KeyboardEvent} e - The native keyboard event / 原生键盘事件
 */
function handleKeydown(e: KeyboardEvent) {
  switch (e.key) {
    case 'ArrowDown':
      // Move selection down, clamped to the last item / 向下移动选择，限制到最后一项
      e.preventDefault()
      activeIndex.value = Math.min(activeIndex.value + 1, filteredCommands.value.length - 1)
      break
    case 'ArrowUp':
      // Move selection up, clamped to the first item / 向上移动选择，限制到第一项
      e.preventDefault()
      activeIndex.value = Math.max(activeIndex.value - 1, 0)
      break
    case 'Enter':
      // Execute the currently highlighted command / 执行当前高亮的命令
      e.preventDefault()
      if (filteredCommands.value[activeIndex.value]) {
        execute(filteredCommands.value[activeIndex.value])
      }
      break
    case 'Escape':
      // Close the palette / 关闭面板
      e.preventDefault()
      close()
      break
  }
}

// ---------------------------------------------------------------------------
// Watchers / 侦听器
// ---------------------------------------------------------------------------

/**
 * When the active index changes, scroll the newly active element into view
 * with smooth animation and nearest-block positioning.
 *
 * 当活动索引发生变化时，将新激活的元素平滑滚动到可视区域，
 * 使用最近块定位。
 */
watch(activeIndex, async () => {
  await nextTick()
  activeEl.value?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
})

/**
 * When the palette opens (visible becomes true), auto-focus the search input
 * so the user can start typing immediately.
 *
 * 当面板打开时（visible 变为 true），自动聚焦搜索输入框，使用户可以立即输入。
 */
watch(() => props.visible, async (v) => {
  if (v) {
    await nextTick()
    inputRef.value?.focus()
  }
})
</script>

<style lang="scss" scoped>
// ==========================================================================
// Command Palette Styles / 命令面板样式
// Golden-accented, frosted-glass aesthetic inspired by VS Code / Spotlight.
// 金色强调、毛玻璃美学，灵感来自 VS Code / Spotlight。
// ==========================================================================

// --------------------------------------------------------------------------
// Overlay backdrop / 遮罩层背景
// --------------------------------------------------------------------------
.palette-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  display: flex; align-items: flex-start; justify-content: center;
  padding-top: 15vh;
  animation: overlayIn 0.2s ease-out;
}

// --------------------------------------------------------------------------
// Dialog card / 对话框卡片
// --------------------------------------------------------------------------
.palette-dialog {
  width: 560px; max-width: 92vw;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(30px) saturate(200%);
  border-radius: 20px;
  box-shadow:
    0 24px 80px rgba(0,0,0,0.2),
    0 8px 32px rgba(0,0,0,0.12),
    inset 0 1px 0 rgba(255,255,255,0.8);
  border: 1px solid rgba(194,164,116,0.15);
  overflow: hidden;
  animation: dialogIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

// --------------------------------------------------------------------------
// Search input row / 搜索输入行
// --------------------------------------------------------------------------
.palette-input-wrap {
  display: flex; align-items: center; gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(194,164,116,0.1);
}

.palette-input {
  flex: 1; border: none; outline: none;
  font-size: 16px; font-weight: 500;
  color: var(--color-text);
  background: transparent;
  font-family: var(--font-sans);
  &::placeholder { color: var(--color-text-muted); }
}

.palette-kbd {
  font-size: 11px; font-weight: 600;
  padding: 3px 8px; border-radius: 6px;
  background: var(--color-bg-alt);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border-light);
  font-family: var(--font-mono);
}

// --------------------------------------------------------------------------
// Results list / 结果列表
// --------------------------------------------------------------------------
.palette-results {
  max-height: 340px; overflow-y: auto;
  padding: 8px;
}

.palette-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border-radius: 12px;
  cursor: pointer; transition: all var(--transition-fast);
  border: 1px solid transparent;

  // Active (keyboard highlight) and hover states share the same style.
  // 激活（键盘高亮）和悬停状态共享相同样式。
  &.active, &:hover {
    background: linear-gradient(135deg, rgba(194,164,116,0.08), rgba(155,135,245,0.06));
    border-color: rgba(194,164,116,0.15);
  }
}

// Command icon badge / 命令图标徽章
.palette-item-icon {
  width: 34px; height: 34px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: white; flex-shrink: 0;
}

// Command text content / 命令文本内容
.palette-item-content {
  flex: 1; min-width: 0;
  display: flex; flex-direction: column;
  .palette-item-label { font-size: 14px; font-weight: 600; color: var(--color-text); }
  .palette-item-desc { font-size: 12px; color: var(--color-text-muted); margin-top: 1px; }
}

// Keyboard shortcut display / 键盘快捷键显示
.palette-item-shortcut {
  display: flex; gap: 4px;
  kbd {
    font-size: 11px; padding: 2px 6px; border-radius: 4px;
    background: var(--color-bg-alt); border: 1px solid var(--color-border-light);
    color: var(--color-text-muted); font-family: var(--font-mono);
  }
}

// Empty state / 空状态
.palette-empty {
  padding: 40px 20px; text-align: center;
  color: var(--color-text-muted); font-size: 14px;
}

// --------------------------------------------------------------------------
// Footer / 底部栏
// --------------------------------------------------------------------------
.palette-footer {
  padding: 10px 20px;
  border-top: 1px solid rgba(194,164,116,0.08);
  background: rgba(248,250,252,0.5);
}

.palette-hints {
  display: flex; gap: 16px; font-size: 12px; color: var(--color-text-muted);
  kbd {
    font-size: 10px; padding: 1px 5px; border-radius: 4px;
    background: var(--color-bg); border: 1px solid var(--color-border-light);
    font-family: var(--font-mono);
  }
}

// --------------------------------------------------------------------------
// Animations / 动画
// --------------------------------------------------------------------------
@keyframes overlayIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes dialogIn { from { opacity: 0; transform: translateY(-10px) scale(0.97); } to { opacity: 1; transform: translateY(0) scale(1); } }

// Transition classes for <transition name="palette"> / <transition name="palette"> 的过渡类
.palette-enter-active { transition: all 0.2s ease-out; }
.palette-leave-active { transition: all 0.15s ease-in; }
.palette-enter-from, .palette-leave-to { opacity: 0; }
.palette-enter-from .palette-dialog { transform: translateY(-10px) scale(0.97); }
</style>
