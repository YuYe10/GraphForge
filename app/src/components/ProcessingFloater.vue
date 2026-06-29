<!--
  ============================================================================
  ProcessingFloater.vue — Processing Task Floater / 处理任务浮层
  ============================================================================
  Role:
    A floating panel anchored to the bottom-right of the viewport that displays
    real-time processing tasks (document ingestion, knowledge extraction, etc.).
    It is driven by the Pinia `processingStore` and supports:
      - A list of tasks with per-task status (processing / completed / failed / cancelled)
      - Animated progress bars for in-flight tasks.
      - AI-mode badges with token statistics.
      - Task cancellation, removal, and "clear finished" bulk action.
      - Minimize/expand toggle and a "View Graph" shortcut.
      - Slide-in/out and task-slide transition animations.

    固定在视口右下角的浮动面板，显示实时处理任务（文档导入、知识提取等）。
    由 Pinia 的 `processingStore` 驱动，支持：
      - 任务列表，每个任务有独立状态（处理中/已完成/失败/已取消）
      - 进行中任务的动画进度条
      - AI 模式徽章及 token 统计
      - 任务取消、移除和"清除已完成"批量操作
      - 最小化/展开切换和"查看图谱"快捷入口
      - 滑入/滑出和任务滑动过渡动画

  Design / 设计要点:
    - Visibility is controlled entirely by the store (`floaterVisible && hasTasks`).
    - Each task has a status-driven color scheme and icon.
    - The footer shows context-aware actions based on task completion counts.
    - Responsive: on mobile (<768px) it spans almost the full viewport width.
    ========================================================================
-->

<template>
  <!--
    Transition wrapper for floater show/hide animation.
    浮层显示/隐藏动画的过渡包装器。
  -->
  <transition name="floater-slide">
    <div
      v-if="processingStore.floaterVisible && processingStore.hasTasks"
      class="processing-floater"
      :class="{ minimized: processingStore.minimized }"
    >
      <!--
        =====================================================================
        Header — title bar with rocket icon and action buttons
        标题栏 — 带有火箭图标和操作按钮
        =====================================================================
      -->
      <div class="floater-header">
        <div class="header-left">
          <n-icon size="18" :component="RocketOutline" class="header-icon" />
          <span class="header-title">
            处理进度
            <!--
              Badge showing the number of currently processing tasks.
              显示当前处理中任务数量的徽章。
            -->
            <n-badge
              v-if="processingStore.processingCount > 0"
              :value="processingStore.processingCount"
              :max="99"
              type="info"
              style="margin-left: 8px"
            />
          </span>
        </div>
        <div class="header-actions">
          <!-- Minimize/expand toggle / 最小化/展开切换 -->
          <n-button text size="small" @click="processingStore.toggleMinimize">
            <template #icon>
              <n-icon :component="processingStore.minimized ? ChevronUpOutline : ChevronDownOutline" />
            </template>
          </n-button>
          <!-- Close button / 关闭按钮 -->
          <n-button text size="small" @click="handleClose">
            <template #icon>
              <n-icon :component="CloseOutline" />
            </template>
          </n-button>
        </div>
      </div>

      <!--
        =====================================================================
        Content — task list with progress, stats, and footer actions
        内容区 — 包含进度、统计和底部操作的任务列表
        =====================================================================
      -->
      <transition name="expand">
        <div v-if="!processingStore.minimized" class="floater-content">
          <n-scrollbar style="max-height: 400px">
            <div class="task-list">
              <!--
                transition-group enables per-task slide animations when tasks
                are added or removed.
                transition-group 在添加或移除任务时启用每个任务的滑动动画。
              -->
              <transition-group name="task-slide">
                <div
                  v-for="task in processingStore.taskList"
                  :key="task.jobId"
                  class="task-item"
                  :class="task.status"
                >
                  <!--
                    Task header — filename + status icon + action buttons
                    任务头部 — 文件名 + 状态图标 + 操作按钮
                  -->
                  <div class="task-header">
                    <div class="task-info">
                      <!-- Status icon (checkmark, alert, clock, etc.) -->
                      <n-icon
                        size="16"
                        class="task-icon"
                        :component="getStatusIcon(task.status)"
                      />
                      <!-- Filename with ellipsis overflow -->
                      <span class="task-filename" :title="task.filename">{{ task.filename }}</span>
                    </div>
                    <div class="task-actions">
                      <!-- Cancel button — only shown for in-progress tasks -->
                      <n-button
                        v-if="task.status === 'processing'"
                        text
                        size="tiny"
                        type="error"
                        @click="handleCancelTask(task.jobId)"
                      >
                        <template #icon>
                          <n-icon :component="StopCircleOutline" />
                        </template>
                      </n-button>
                      <!-- Dismiss button — shown for completed/failed/cancelled -->
                      <n-button
                        v-if="task.status !== 'processing'"
                        text
                        size="tiny"
                        @click="processingStore.removeTask(task.jobId)"
                      >
                        <template #icon>
                          <n-icon :component="CloseOutline" />
                        </template>
                      </n-button>
                    </div>
                  </div>

                  <!--
                    Progress bar — only visible during active processing.
                    进度条 — 仅在活跃处理中可见。
                  -->
                  <div v-if="task.status === 'processing'" class="task-progress">
                    <div class="progress-info">
                      <span class="progress-message">{{ task.message || '处理中...' }}</span>
                      <span class="progress-percent">{{ task.progress }}%</span>
                    </div>
                    <n-progress
                      type="line"
                      :percentage="task.progress"
                      :show-indicator="false"
                      :height="6"
                      border-radius="3px"
                      :color="getProgressColor(task.status)"
                    />
                  </div>

                  <!--
                    Status message — shown for non-processing tasks.
                    状态消息 — 对非处理中的任务显示。
                  -->
                  <div v-else class="task-status">
                    <span class="status-message">{{ task.message || getStatusMessage(task.status) }}</span>
                  </div>

                  <!--
                    AI Mode badges — shown when the task uses AI for extraction.
                    AI 模式徽章 — 当任务使用 AI 进行提取时显示。
                  -->
                  <div v-if="task.aiMode" class="ai-mode-badge">
                    <n-tag type="success" size="tiny" :bordered="false">
                      <template #icon>
                        <n-icon :component="SparklesOutline" />
                      </template>
                      AI 模式
                    </n-tag>
                    <!-- Model name (e.g., "gpt-4", "qwen-max") -->
                    <n-tag v-if="task.aiStats?.model" type="info" size="tiny" :bordered="false">
                      {{ task.aiStats.model }}
                    </n-tag>
                  </div>

                  <!--
                    Task stats — shown for completed tasks (chunks, triplets, concepts).
                    任务统计 — 对已完成任务显示（文本块、三元组、概念）。
                  -->
                  <div v-if="task.status === 'completed' && task.stats" class="task-stats">
                    <div class="stat-chip">
                      <span class="stat-label">文本块</span>
                      <span class="stat-value">{{ task.stats.chunks }}</span>
                    </div>
                    <div class="stat-chip">
                      <span class="stat-label">三元组</span>
                      <span class="stat-value">{{ task.stats.triplets }}</span>
                    </div>
                    <div class="stat-chip">
                      <span class="stat-label">概念</span>
                      <span class="stat-value">{{ task.stats.concepts }}</span>
                    </div>
                  </div>

                  <!--
                    AI token usage — shown for completed AI-mode tasks.
                    AI token 用量 — 对已完成的 AI 模式任务显示。
                  -->
                  <div v-if="task.status === 'completed' && task.aiMode && task.aiStats" class="ai-tokens-stats">
                    <div class="tokens-chip">
                      <span class="tokens-icon">📊</span>
                      <span class="tokens-label">Tokens:</span>
                      <span class="tokens-value">{{ formatNumber(task.aiStats.totalTokens) }}</span>
                    </div>
                  </div>
                </div>
              </transition-group>
            </div>
          </n-scrollbar>

          <!--
            =================================================================
            Footer — bulk actions
            底部栏 — 批量操作
            =================================================================
          -->
          <div class="floater-footer">
            <!-- Clear finished (completed + failed) tasks / 清除已完成/失败的任务 -->
            <n-button
              v-if="processingStore.completedCount > 0 || processingStore.failedCount > 0"
              text
              size="small"
              @click="processingStore.clearFinishedTasks"
            >
              清除已完成
            </n-button>
            <!-- Quick navigation to the graph visualization page -->
            <n-button
              v-if="processingStore.completedCount > 0"
              type="primary"
              size="small"
              @click="handleViewGraph"
            >
              查看图谱
            </n-button>
          </div>
        </div>
      </transition>
    </div>
  </transition>
</template>

<script setup lang="ts">
/**
 * ============================================================================
 * ProcessingFloater — Script
 * ============================================================================
 *
 * Bridges the Pinia processing store to the UI layer. Provides helper
 * utilities for status-to-icon/color/message mapping, task cancellation,
 * and number formatting.
 *
 * 将 Pinia 处理 store 桥接到 UI 层。提供状态到图标/颜色/消息的映射、
 * 任务取消和数字格式化等辅助工具。
 */

import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useProcessingStore } from '@/stores/processing'
import {
  RocketOutline,
  CloseOutline,
  ChevronUpOutline,
  ChevronDownOutline,
  CheckmarkCircleOutline,
  AlertCircleOutline,
  TimeOutline,
  SparklesOutline,
  StopCircleOutline
} from '@vicons/ionicons5'

const router = useRouter()
const message = useMessage()
const processingStore = useProcessingStore()

// ---------------------------------------------------------------------------
// Status helpers / 状态辅助函数
// ---------------------------------------------------------------------------

/**
 * Maps a task status to its corresponding Ionicon5 icon component.
 * @param {'processing'|'completed'|'failed'|'cancelled'} status - Current task status / 当前任务状态
 * @returns {any} Ionicon5 component reference / Ionicon5 组件引用
 */
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return CheckmarkCircleOutline
    case 'failed':
      return AlertCircleOutline
    case 'cancelled':
      return StopCircleOutline
    default:
      return TimeOutline
  }
}

/**
 * Returns a localized status message for a given status.
 * @param {'processing'|'completed'|'failed'|'cancelled'} status - Current task status / 当前任务状态
 * @returns {string} Localized status text / 本地化的状态文本
 */
const getStatusMessage = (status: string) => {
  switch (status) {
    case 'completed':
      return '处理完成'
    case 'failed':
      return '处理失败'
    case 'cancelled':
      return '任务已取消'
    default:
      return '处理中'
  }
}

/**
 * Maps a task status to a progress bar color.
 * @param {'processing'|'completed'|'failed'|'cancelled'} status - Current task status / 当前任务状态
 * @returns {string} CSS color value / CSS 颜色值
 */
const getProgressColor = (status: string) => {
  switch (status) {
    case 'completed':
      return '#18a058'  // Green / 绿色
    case 'failed':
      return '#d03050'  // Red / 红色
    default:
      return '#c2a474'  // Gold (processing) / 金色（处理中）
  }
}

// ---------------------------------------------------------------------------
// Actions / 操作
// ---------------------------------------------------------------------------

/**
 * Cancels a processing task via the store and shows a success/error toast.
 * 通过 store 取消处理任务并显示成功/失败提示。
 * @param {string} jobId - The job identifier to cancel / 要取消的任务标识
 */
const handleCancelTask = async (jobId: string) => {
  const success = await processingStore.cancelTask(jobId)
  if (success) {
    message.success('任务已取消')
  } else {
    message.error('取消任务失败')
  }
}

/**
 * Closes the floater. If tasks are still processing, shows a warning instead.
 * 关闭浮层。如果仍有任务在处理中，则显示警告。
 */
const handleClose = () => {
  if (processingStore.processingCount > 0) {
    // Prevent accidental close while tasks are running / 防止在任务运行时意外关闭
    message.warning('仍有任务正在处理中')
    return
  }
  processingStore.hideFloater()
}

/**
 * Navigates to the graph visualization page.
 * 导航到图谱可视化页面。
 */
const handleViewGraph = () => {
  router.push('/graph')
}

// ---------------------------------------------------------------------------
// Utilities / 工具函数
// ---------------------------------------------------------------------------

/**
 * Formats a number with locale-aware thousand separators (zh-CN).
 * @param {number | undefined} num - The number to format / 要格式化的数字
 * @returns {string} Formatted number string / 格式化后的数字字符串
 */
const formatNumber = (num: number | undefined) => {
  if (!num) return '0'
  return num.toLocaleString('zh-CN')
}
</script>

<style lang="scss" scoped>
// ==========================================================================
// Processing Floater Styles / 处理任务浮层样式
// Frosted-glass panel anchored to bottom-right of the viewport.
// 固定在视口右下角的毛玻璃面板。
// ==========================================================================

.processing-floater {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 420px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 0.95) 100%);
  border-radius: 16px;
  box-shadow:
    0 12px 48px rgba(0, 0, 0, 0.12),
    0 4px 16px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(194, 164, 116, 0.2);
  backdrop-filter: blur(20px);
  z-index: 2000;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  // Minimized state: only the header is visible.
  // 最小化状态：仅头部可见。
  &.minimized {
    .floater-content {
      display: none;
    }
  }

  // Elevation increase on hover / 悬停时增加阴影深度
  &:hover {
    box-shadow:
      0 16px 56px rgba(0, 0, 0, 0.15),
      0 6px 20px rgba(0, 0, 0, 0.1);
  }

  // --------------------------------------------------------------------------
  // Header / 头部
  // --------------------------------------------------------------------------
  .floater-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid rgba(194, 164, 116, 0.15);
    background: linear-gradient(135deg, rgba(194, 164, 116, 0.08) 0%, rgba(155, 135, 245, 0.05) 100%);

    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;

      .header-icon {
        color: #c2a474;
      }

      .header-title {
        font-size: 14px;
        font-weight: 600;
        color: #1e293b;
        display: flex;
        align-items: center;
      }
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 4px;

      :deep(.n-button) {
        color: #64748b;

        &:hover {
          color: #1e293b;
          background: rgba(0, 0, 0, 0.05);
        }
      }
    }
  }

  // --------------------------------------------------------------------------
  // Content area — appears below header when not minimized
  // 内容区域 — 未最小化时显示在头部下方
  // --------------------------------------------------------------------------
  .floater-content {
    overflow: hidden;
    animation: expand 0.3s ease-out;

    .task-list {
      padding: 12px;

      .task-item {
        padding: 12px;
        margin-bottom: 8px;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(194, 164, 116, 0.15);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

        &:last-child {
          margin-bottom: 0;
        }

        // Hover lift effect / 悬停抬升效果
        &:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
          transform: translateY(-2px);
        }

        // Status-specific border and background colors / 状态特定的边框和背景颜色
        &.processing { border-color: rgba(194, 164, 116, 0.3); background: linear-gradient(135deg, rgba(194, 164, 116, 0.05) 0%, rgba(155, 135, 245, 0.05) 100%); }
        &.completed  { border-color: rgba(24, 160, 88, 0.2);   background: rgba(24, 160, 88, 0.05); }
        &.failed     { border-color: rgba(208, 48, 80, 0.2);   background: rgba(208, 48, 80, 0.05); }
        &.cancelled  { border-color: rgba(100, 116, 139, 0.2); background: rgba(100, 116, 139, 0.05); }

        .task-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 8px;

          .task-info {
            display: flex;
            align-items: center;
            gap: 8px;
            flex: 1;
            min-width: 0;

            .task-icon {
              flex-shrink: 0;

              &.processing { color: #c2a474; }
              &.completed  { color: #18a058; }
              &.failed     { color: #d03050; }
              &.cancelled  { color: #64748b; }
            }

            .task-actions {
              display: flex;
              align-items: center;
              gap: 4px;
            }

            .task-filename {
              font-size: 13px;
              font-weight: 600;
              color: #1e293b;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
            }
          }
        }

        // Progress bar area / 进度条区域
        .task-progress {
          .progress-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;

            .progress-message {
              font-size: 12px;
              color: #64748b;
              font-weight: 500;
            }

            .progress-percent {
              font-size: 12px;
              font-weight: 700;
              color: #c2a474;
            }
          }
        }

        // Status message text / 状态消息文本
        .task-status {
          .status-message {
            font-size: 12px;
            color: #64748b;
            font-weight: 500;
          }
        }

        // AI mode tags / AI 模式标签
        .ai-mode-badge {
          display: flex;
          gap: 6px;
          margin-top: 8px;
          flex-wrap: wrap;
        }

        // Stats chips (chunks, triplets, concepts) / 统计标签
        .task-stats {
          display: flex;
          gap: 6px;
          margin-top: 8px;
          flex-wrap: wrap;

          .stat-chip {
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 4px 8px;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 6px;
            border: 1px solid rgba(194, 164, 116, 0.2);

            .stat-label {
              font-size: 11px;
              color: #64748b;
              font-weight: 500;
            }

            .stat-value {
              font-size: 12px;
              font-weight: 700;
              color: #c2a474;
            }
          }
        }

        // AI token statistics / AI token 统计
        .ai-tokens-stats {
          margin-top: 8px;

          .tokens-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: linear-gradient(135deg, rgba(194, 164, 116, 0.1) 0%, rgba(155, 135, 245, 0.1) 100%);
            border-radius: 8px;
            border: 1px solid rgba(194, 164, 116, 0.25);

            .tokens-icon {
              font-size: 14px;
            }

            .tokens-label {
              font-size: 11px;
              color: #64748b;
              font-weight: 500;
            }

            .tokens-value {
              font-size: 13px;
              font-weight: 700;
              background: linear-gradient(135deg, #c2a474 0%, #9b87f5 100%);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
              background-clip: text;
            }
          }
        }
      }
    }
  }

  // --------------------------------------------------------------------------
  // Footer / 底部栏
  // --------------------------------------------------------------------------
  .floater-footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
    padding: 12px 16px;
    border-top: 1px solid rgba(194, 164, 116, 0.15);
    background: rgba(248, 250, 252, 0.5);

    :deep(.n-button) {
      font-size: 12px;
    }
  }
}

// ==========================================================================
// Animations / 动画
// ==========================================================================

// Floater slide in/out / 浮层滑入/滑出
.floater-slide-enter-active,
.floater-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.floater-slide-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.floater-slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

// Per-task slide animation / 单个任务滑动动画
.task-slide-enter-active,
.task-slide-leave-active {
  transition: all 0.3s ease;
}

.task-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.task-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

// Content expand/collapse / 内容展开/折叠
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}

// Content expand keyframe / 内容展开关键帧
@keyframes expand {
  from {
    max-height: 0;
    opacity: 0;
  }
  to {
    max-height: 500px;
    opacity: 1;
  }
}

// ==========================================================================
// Responsive / 响应式
// ==========================================================================
@media (max-width: 768px) {
  .processing-floater {
    width: calc(100vw - 48px);
    right: 24px;
    left: 24px;
  }
}
</style>
