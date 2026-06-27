<template>
  <teleport to="body">
    <transition name="palette">
      <div v-if="visible" class="palette-overlay" @click.self="close">
        <div class="palette-dialog" @click.stop>
          <!-- Search input -->
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

          <!-- Results -->
          <div class="palette-results">
            <template v-if="filteredCommands.length > 0">
              <div
                v-for="(cmd, idx) in filteredCommands"
                :key="cmd.key"
                :ref="(el: any) => { if (idx === activeIndex) activeEl = el }"
                :class="['palette-item', { active: idx === activeIndex }]"
                @click="execute(cmd)"
                @mousemove="activeIndex = idx"
              >
                <div class="palette-item-icon" :style="{ background: cmd.bg }">
                  <n-icon size="16"><component :is="cmd.icon" /></n-icon>
                </div>
                <div class="palette-item-content">
                  <span class="palette-item-label">{{ cmd.label }}</span>
                  <span class="palette-item-desc">{{ cmd.desc }}</span>
                </div>
                <div class="palette-item-shortcut" v-if="cmd.shortcut">
                  <kbd v-for="k in cmd.shortcut" :key="k">{{ k }}</kbd>
                </div>
              </div>
            </template>
            <div v-else class="palette-empty">
              <span>未找到匹配的命令</span>
            </div>
          </div>

          <!-- Footer -->
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
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  SearchOutline, GridOutline, CloudUploadOutline,
  DocumentTextOutline, OptionsOutline, GitNetworkOutline,
  CodeSlashOutline, TimeOutline, SettingsOutline,
  ChatbubbleEllipsesOutline, RefreshOutline
} from '@vicons/ionicons5'

const router = useRouter()

interface Command {
  key: string
  label: string
  desc: string
  icon: any
  bg: string
  shortcut?: string[]
  action: () => void
}

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ 'update:visible': [boolean] }>()

const query = ref('')
const activeIndex = ref(0)
const inputRef = ref<HTMLInputElement>()
const activeEl = ref<HTMLElement>()

const commands: Command[] = [
  { key: 'dashboard', label: '仪表盘', desc: '查看知识图谱全景', icon: GridOutline, bg: 'linear-gradient(135deg,#d4af37,#b8860b)', shortcut: ['G','D'], action: () => router.push('/') },
  { key: 'upload', label: '知识构建', desc: '上传文档构建知识', icon: CloudUploadOutline, bg: 'linear-gradient(135deg,#c9a668,#9a7509)', shortcut: ['G','U'], action: () => router.push('/knowledge') },
  { key: 'documents', label: '文档管理', desc: '查看已上传文档', icon: DocumentTextOutline, bg: 'linear-gradient(135deg,#3b82f6,#1e40af)', shortcut: ['G','M'], action: () => router.push('/documents') },
  { key: 'cards', label: '知识卡片', desc: '管理知识卡片', icon: OptionsOutline, bg: 'linear-gradient(135deg,#9b87f5,#7c6ae0)', shortcut: ['G','K'], action: () => router.push('/knowledge-card') },
  { key: 'graph', label: '图谱可视化', desc: '交互式知识图谱', icon: GitNetworkOutline, bg: 'linear-gradient(135deg,#10b981,#059669)', shortcut: ['G','G'], action: () => router.push('/graph') },
  { key: 'query', label: '知识查询', desc: 'Cypher 查询图谱', icon: CodeSlashOutline, bg: 'linear-gradient(135deg,#3b82f6,#2563eb)', shortcut: ['G','Q'], action: () => router.push('/query') },
  { key: 'status', label: '处理状态', desc: '查看任务进度', icon: TimeOutline, bg: 'linear-gradient(135deg,#f59e0b,#d97706)', shortcut: ['G','S'], action: () => router.push('/status') },
  { key: 'settings', label: '系统设置', desc: '配置 AI 与数据库', icon: SettingsOutline, bg: 'linear-gradient(135deg,#8b5cf6,#6d28d9)', action: () => router.push('/settings') },
  { key: 'qa', label: '智能问答', desc: '向知识图谱提问', icon: ChatbubbleEllipsesOutline, bg: 'linear-gradient(135deg,#ec4899,#db2777)', action: () => { (window as any).__openQA?.(); close() } },
  { key: 'refresh', label: '刷新当前页面', desc: '重新加载数据', icon: RefreshOutline, bg: 'linear-gradient(135deg,#64748b,#475569)', shortcut: ['Ctrl','R'], action: () => window.location.reload() },
]

const filteredCommands = computed(() => {
  if (!query.value.trim()) return commands
  const q = query.value.toLowerCase()
  return commands.filter(c =>
    c.label.toLowerCase().includes(q) ||
    c.desc.toLowerCase().includes(q) ||
    c.key.toLowerCase().includes(q)
  )
})

function close() {
  emit('update:visible', false)
  query.value = ''
  activeIndex.value = 0
}

function execute(cmd: Command) {
  cmd.action()
  close()
}

function handleKeydown(e: KeyboardEvent) {
  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      activeIndex.value = Math.min(activeIndex.value + 1, filteredCommands.value.length - 1)
      break
    case 'ArrowUp':
      e.preventDefault()
      activeIndex.value = Math.max(activeIndex.value - 1, 0)
      break
    case 'Enter':
      e.preventDefault()
      if (filteredCommands.value[activeIndex.value]) {
        execute(filteredCommands.value[activeIndex.value])
      }
      break
    case 'Escape':
      e.preventDefault()
      close()
      break
  }
}

// Scroll active into view
watch(activeIndex, async () => {
  await nextTick()
  activeEl.value?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
})

// Focus input on open
watch(() => props.visible, async (v) => {
  if (v) {
    await nextTick()
    inputRef.value?.focus()
  }
})
</script>

<style lang="scss" scoped>
.palette-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  display: flex; align-items: flex-start; justify-content: center;
  padding-top: 15vh;
  animation: overlayIn 0.2s ease-out;
}

.palette-dialog {
  width: 560px; max-width: 92vw;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(30px) saturate(200%);
  border-radius: 20px;
  box-shadow: 0 24px 80px rgba(0,0,0,0.2), 0 8px 32px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.8);
  border: 1px solid rgba(194,164,116,0.15);
  overflow: hidden;
  animation: dialogIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

// Input
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

// Results
.palette-results {
  max-height: 340px; overflow-y: auto;
  padding: 8px;
}

.palette-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border-radius: 12px;
  cursor: pointer; transition: all var(--transition-fast);
  border: 1px solid transparent;

  &.active, &:hover {
    background: linear-gradient(135deg, rgba(194,164,116,0.08), rgba(155,135,245,0.06));
    border-color: rgba(194,164,116,0.15);
  }
}

.palette-item-icon {
  width: 34px; height: 34px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: white; flex-shrink: 0;
}

.palette-item-content {
  flex: 1; min-width: 0;
  display: flex; flex-direction: column;
  .palette-item-label { font-size: 14px; font-weight: 600; color: var(--color-text); }
  .palette-item-desc { font-size: 12px; color: var(--color-text-muted); margin-top: 1px; }
}

.palette-item-shortcut {
  display: flex; gap: 4px;
  kbd {
    font-size: 11px; padding: 2px 6px; border-radius: 4px;
    background: var(--color-bg-alt); border: 1px solid var(--color-border-light);
    color: var(--color-text-muted); font-family: var(--font-mono);
  }
}

.palette-empty {
  padding: 40px 20px; text-align: center;
  color: var(--color-text-muted); font-size: 14px;
}

// Footer
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

// Animations
@keyframes overlayIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes dialogIn { from { opacity: 0; transform: translateY(-10px) scale(0.97); } to { opacity: 1; transform: translateY(0) scale(1); } }

.palette-enter-active { transition: all 0.2s ease-out; }
.palette-leave-active { transition: all 0.15s ease-in; }
.palette-enter-from, .palette-leave-to { opacity: 0; }
.palette-enter-from .palette-dialog { transform: translateY(-10px) scale(0.97); }
</style>
