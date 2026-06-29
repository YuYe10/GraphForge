/**
 * GraphForge — Processing Store (Pinia)
 * GraphForge — 处理任务状态存储 (Pinia)
 *
 * Tracks the lifecycle of document-processing jobs submitted to the backend.
 * Provides an in-memory task map, a polling system that periodically queries
 * the backend for job status updates, computed aggregations (counts by
 * status), and UI floater visibility controls.
 *
 * 跟踪提交到后端的文档处理作业的生命周期。
 * 提供内存中的任务映射表、定时轮询查询后台任务状态的轮询系统、
 * 按状态分类的聚合计算属性，以及 UI 漂浮窗的可见性控制。
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getJobStatus } from '@/api/services'
import type { JobStatus } from '@/api/services'
import { cancelJob } from '@/api/index'

/**
 * Represents a single document-processing task within the store.
 * 表示存储中的单个文档处理任务。
 *
 * @property jobId       - Backend job identifier / 后端作业标识符
 * @property documentId  - Associated document identifier / 关联的文档标识符
 * @property filename    - Original file name (human-readable) / 原始文件名（可读）
 * @property status      - Current processing status / 当前处理状态
 * @property progress    - Progress percentage 0-100 / 进度百分比 0-100
 * @property message     - Status message or description / 状态消息或描述
 * @property stats       - Optional processing statistics (chunks, triplets, concepts)
 *                         可选的统计信息（分块数、三元组数、概念数）
 * @property aiMode      - Whether AI-assisted mode is enabled / 是否启用 AI 辅助模式
 * @property aiStats     - Optional AI usage statistics / 可选的 AI 使用统计
 * @property insights    - Optional list of insight strings / 可选的洞察列表
 * @property createdAt   - Unix timestamp (ms) when the task was created
 *                         任务创建时的 Unix 时间戳（毫秒）
 */
export interface ProcessingTask {
  jobId: string
  documentId: string
  filename: string
  status: 'processing' | 'completed' | 'failed' | 'cancelled'
  progress: number
  message: string
  stats?: {
    chunks: number
    triplets: number
    concepts: number
  }
  aiMode?: boolean
  aiStats?: {
    totalTokens?: number
    promptTokens?: number
    completionTokens?: number
    model?: string
  }
  insights?: string[]
  createdAt: number
}

/**
 * Pinia store that manages the lifecycle of document-processing tasks.
 * Pinia 存储，管理文档处理任务的生命周期。
 *
 * @returns {object} Reactive state, computed properties, and actions:
 *
 * State / 状态:
 *   - tasks          — Map of jobId → ProcessingTask / 任务映射表
 *   - floaterVisible — Whether the processing floater UI is shown / 处理浮窗是否可见
 *   - minimized      — Whether the floater is minimised / 浮窗是否最小化
 *
 * Computed / 计算属性:
 *   - hasTasks         — Whether any tasks exist / 是否存在任务
 *   - processingCount  — Number of tasks currently processing / 处理中的任务数
 *   - completedCount   — Number of completed tasks / 已完成的任务数
 *   - failedCount      — Number of failed tasks / 失败的任务数
 *   - taskList         — Tasks sorted by creation time (newest first) / 按创建时间排序（最新在前）
 *
 * Actions / 动作:
 *   - addTask            — Add a new task and begin polling / 添加新任务并开始轮询
 *   - updateTask         — Partially update a task's fields / 部分更新任务字段
 *   - removeTask         — Remove a task and stop its poll timer / 移除任务并停止轮询
 *   - clearFinishedTasks — Remove all completed / failed / cancelled tasks / 清除已结束的任务
 *   - cancelTask         — Cancel a running job on the backend / 取消后端正在运行的作业
 *   - toggleFloater      — Toggle floater visibility / 切换浮窗可见性
 *   - showFloater        — Show the floater / 显示浮窗
 *   - hideFloater        — Hide the floater / 隐藏浮窗
 *   - toggleMinimize     — Toggle floater minimised state / 切换浮窗最小化状态
 */
export const useProcessingStore = defineStore('processing', () => {
  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------

  /** Map of jobId -> ProcessingTask, holding all known tasks in memory. */
  const tasks = ref<Map<string, ProcessingTask>>(new Map())

  /**
   * Map of jobId -> setInterval timer ID.
   * Each active job gets a 1-second poll interval while it is processing.
   * 每个活跃任务都有一个 1 秒的轮询间隔。
   */
  const pollTimers = ref<Map<string, number>>(new Map())

  /** Whether the processing status floater is visible. */
  const floaterVisible = ref(false)

  /** Whether the floater panel is in its compact / minimised state. */
  const minimized = ref(false)

  // ---------------------------------------------------------------------------
  // Computed properties
  // ---------------------------------------------------------------------------

  /** True when at least one task exists in the store. */
  const hasTasks = computed(() => tasks.value.size > 0)

  /** Number of tasks whose status is 'processing'. */
  const processingCount = computed(() => {
    return Array.from(tasks.value.values()).filter(
      task => task.status === 'processing'
    ).length
  })

  /** Number of tasks whose status is 'completed'. */
  const completedCount = computed(() => {
    return Array.from(tasks.value.values()).filter(
      task => task.status === 'completed'
    ).length
  })

  /** Number of tasks whose status is 'failed'. */
  const failedCount = computed(() => {
    return Array.from(tasks.value.values()).filter(
      task => task.status === 'failed'
    ).length
  })

  /**
   * All tasks sorted by creation time in descending order (newest first).
   * 所有任务按创建时间降序排列（最新在前）。
   */
  const taskList = computed(() => {
    return Array.from(tasks.value.values())
      .sort((a, b) => b.createdAt - a.createdAt)
  })

  // ---------------------------------------------------------------------------
  // Task CRUD actions
  // ---------------------------------------------------------------------------

  /**
   * Add a new processing task to the store and start polling its status.
   * 向存储中添加新的处理任务并开始轮询其状态。
   *
   * Automatically stamps the current timestamp as `createdAt` and makes the
   * floater visible.
   * 自动将当前时间戳标记为 `createdAt` 并使浮窗可见。
   *
   * @param task — Task data (without `createdAt`, which is auto-filled)
   *               任务数据（不含 `createdAt`，该字段自动填充）
   */
  const addTask = (task: Omit<ProcessingTask, 'createdAt'>) => {
    const fullTask = {
      ...task,
      createdAt: Date.now()
    }
    tasks.value.set(task.jobId, fullTask)
    floaterVisible.value = true
    startPolling(task.jobId)
  }

  /**
   * Partially update an existing task's fields by jobId.
   * 按 jobId 部分更新现有任务的字段。
   *
   * @param jobId   — The job to update / 要更新的作业 ID
   * @param updates — A partial ProcessingTask object to merge in / 要合并的部分 ProcessingTask 对象
   */
  const updateTask = (jobId: string, updates: Partial<ProcessingTask>) => {
    const task = tasks.value.get(jobId)
    if (task) {
      tasks.value.set(jobId, { ...task, ...updates })
    }
  }

  /**
   * Remove a task from the store and stop its poll timer.
   * 从存储中移除任务并停止其轮询定时器。
   *
   * Automatically hides the floater when the last task is removed.
   * 移除最后一个任务时自动隐藏浮窗。
   *
   * @param jobId — The job to remove / 要移除的作业 ID
   */
  const removeTask = (jobId: string) => {
    stopPolling(jobId)
    tasks.value.delete(jobId)
    if (tasks.value.size === 0) {
      floaterVisible.value = false
    }
  }

  /**
   * Remove all tasks that have reached a terminal status
   * (completed, failed, or cancelled).
   * 移除所有已到达终态（completed、failed 或 cancelled）的任务。
   *
   * Leaves actively processing tasks untouched so they continue to update.
   * 保留正在处理中的任务，使其继续更新。
   */
  const clearFinishedTasks = () => {
    const toRemove: string[] = []
    tasks.value.forEach((task, jobId) => {
      if (task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled') {
        toRemove.push(jobId)
      }
    })
    toRemove.forEach(jobId => removeTask(jobId))
  }

  /**
   * Cancel a running job on the backend and update local state.
   * 取消后端正在运行的作业并更新本地状态。
   *
   * Sends a cancellation request to the API, then marks the task as
   * 'cancelled' locally and stops polling.
   * 向 API 发送取消请求，然后本地将任务标记为 'cancelled' 并停止轮询。
   *
   * @param jobId — The job to cancel / 要取消的作业 ID
   * @returns `true` if cancellation succeeded, `false` on error
   *          取消成功返回 `true`，出错返回 `false`
   */
  const cancelTask = async (jobId: string) => {
    try {
      await cancelJob(jobId)

      // Update local task state immediately after successful backend cancellation
      // 后端取消成功后立即更新本地任务状态
      const task = tasks.value.get(jobId)
      if (task) {
        updateTask(jobId, {
          status: 'cancelled',
          message: '任务已取消'  // "Task cancelled"
        })
        stopPolling(jobId)
      }

      return true
    } catch (error) {
      console.error(`Failed to cancel job ${jobId}:`, error)
      return false
    }
  }

  // ---------------------------------------------------------------------------
  // Polling system
  // ---------------------------------------------------------------------------

  /**
   * Start polling the backend for job status updates at a 1-second interval.
   * 开始以 1 秒间隔轮询后端获取作业状态更新。
   *
   * Fires an immediate request on start, then continues every 1000 ms.
   * Polling stops automatically once the job reaches a terminal status
   * (completed, failed, or cancelled).
   * 启动时立即发送一次请求，之后每 1000 ms 执行一次。
   * 当作业到达终态（completed、failed 或 cancelled）时自动停止轮询。
   *
   * @param jobId — The job to poll / 要轮询的作业 ID
   */
  const startPolling = (jobId: string) => {
    // Clear any existing timer for this job to avoid duplicate intervals
    // 清除该作业的现有定时器，避免重复的间隔
    stopPolling(jobId)

    const poll = async () => {
      try {
        const status: JobStatus = await getJobStatus(jobId)
        const task = tasks.value.get(jobId)

        if (!task) return

        // Update progress, message, statistics, and AI info from the response
        // 根据响应更新进度、消息、统计数据和 AI 信息
        updateTask(jobId, {
          progress: status.progress || 0,
          message: status.message || '',
          stats: status.stats,
          aiMode: status.ai_mode,
          aiStats: status.ai_stats ? {
            totalTokens: status.ai_stats.total_tokens,
            promptTokens: status.ai_stats.prompt_tokens,
            completionTokens: status.ai_stats.completion_tokens,
            model: status.ai_stats.model
          } : undefined,
          insights: status.insights
        })

        // Handle terminal states: stop polling once the job finishes
        // 处理终态：作业完成后停止轮询
        if (status.status === 'completed') {
          updateTask(jobId, { status: 'completed' })
          stopPolling(jobId)
        } else if (status.status === 'failed') {
          updateTask(jobId, {
            status: 'failed',
            message: status.error || status.message || '处理失败'  // "Processing failed"
          })
          stopPolling(jobId)
        } else if (status.status === 'cancelled') {
          updateTask(jobId, {
            status: 'cancelled',
            message: status.message || '任务已取消'  // "Task cancelled"
          })
          stopPolling(jobId)
        }
      } catch (error) {
        console.error(`Failed to poll job ${jobId}:`, error)
      }
    }

    // Execute immediately, then repeat every second
    // 立即执行一次，之后每秒重复
    poll()

    const timer = window.setInterval(poll, 1000)
    pollTimers.value.set(jobId, timer)
  }

  /**
   * Stop polling for a specific job and release its interval timer.
   * 停止对特定作业的轮询并释放其间隔定时器。
   *
   * Safe to call even if no polling is active for the given jobId.
   * 即使给定 jobId 没有活跃的轮询，调用也是安全的。
   *
   * @param jobId — The job to stop polling / 要停止轮询的作业 ID
   */
  const stopPolling = (jobId: string) => {
    const timer = pollTimers.value.get(jobId)
    if (timer) {
      clearInterval(timer)
      pollTimers.value.delete(jobId)
    }
  }

  /**
   * Stop all active poll timers. Useful when the store is reset or
   * the user navigates away from pages that trigger polling.
   * 停止所有活跃的轮询定时器。在重置存储或用户离开触发轮询的页面时使用。
   */
  const stopAllPolling = () => {
    pollTimers.value.forEach((timer) => clearInterval(timer))
    pollTimers.value.clear()
  }

  // ---------------------------------------------------------------------------
  // Floater UI controls
  // ---------------------------------------------------------------------------

  /** Toggle the processing status floater between visible and hidden. */
  const toggleFloater = () => {
    floaterVisible.value = !floaterVisible.value
  }

  /** Make the processing status floater visible. */
  const showFloater = () => {
    floaterVisible.value = true
  }

  /** Hide the processing status floater. */
  const hideFloater = () => {
    floaterVisible.value = false
  }

  /** Toggle the floater between its normal and compact (minimised) state. */
  const toggleMinimize = () => {
    minimized.value = !minimized.value
  }

  return {
    tasks,
    floaterVisible,
    minimized,
    hasTasks,
    processingCount,
    completedCount,
    failedCount,
    taskList,
    addTask,
    updateTask,
    removeTask,
    clearFinishedTasks,
    cancelTask,
    startPolling,
    stopPolling,
    stopAllPolling,
    toggleFloater,
    showFloater,
    hideFloater,
    toggleMinimize
  }
})
