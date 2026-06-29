<template>
  <div class="status-page">
    <div class="page-bg"></div>

    <!-- Header -->
    <div class="status-header glass-card">
      <h1 class="status-title gradient-text-amber">{{ t('status.title') }}</h1>
      <p class="status-subtitle">查看文档处理任务的实时状态 · Job Status Monitor</p>
    </div>

    <n-card class="status-card glass-card" :bordered="false">
      <n-space :size="16" style="margin-bottom: 20px" align="end">
        <n-form-item label="任务 ID" style="margin-bottom:0">
          <n-input v-model:value="jobId" :placeholder="t('status.job_id_help')" style="width: 320px" />
        </n-form-item>
        <n-button type="primary" :loading="checking" @click="checkStatus" size="large">
          <template #icon><n-icon><search-outline /></n-icon></template>
          {{ t('status.check_status') }}
        </n-button>
      </n-space>

      <n-divider v-if="statusData" />

      <div v-if="statusData" class="status-result">
        <n-space vertical :size="16">
          <n-card size="small" :title="t('status.status')">
            <n-space :size="20">
              <div class="status-item">
                <span class="si-label">{{ t('status.status') }}:</span>
                <n-tag :type="getStatusType(statusData.status)" round size="large">
                  <template #icon><span class="status-dot" :class="statusData.status"></span></template>
                  {{ getStatusText(statusData.status) }}
                </n-tag>
              </div>
              <div class="status-item">
                <span class="si-label">{{ t('status.progress') }}:</span>
                <n-progress v-if="statusData.progress !== undefined" type="circle" :percentage="statusData.progress || 0" :status="statusData.status === 'failed' ? 'error' : statusData.status === 'completed' ? 'success' : 'default'" :width="60" />
                <n-text v-else>N/A</n-text>
              </div>
            </n-space>
          </n-card>
          <n-card v-if="statusData.statistics" size="small" :title="t('status.statistics')">
            <n-code :code="JSON.stringify(statusData.statistics, null, 2)" language="json" />
          </n-card>
          <n-card v-if="statusData.result" size="small" :title="t('status.view_full_result')">
            <n-code :code="JSON.stringify(statusData.result, null, 2)" language="json" />
          </n-card>
        </n-space>
      </div>

      <n-empty v-else-if="!checking && !jobId" :description="t('status.enter_job_id')" size="large">
        <template #icon><n-icon size="48"><document-text-outline /></n-icon></template>
      </n-empty>
    </n-card>
  </div>
</template>

<script setup lang="ts">
/**
 * Status.vue - Job Status Checker View
 * 任务状态查询视图
 *
 * Purpose / 功能说明:
 *   Simple job status checker that retrieves and displays processing job information
 *   by job ID. Reads the `jobId` query parameter from the URL on mount for deep-linking.
 *   Displays job status (with color-coded tag), circular progress indicator,
 *   and raw JSON views for statistics and full results.
 *   简单的任务状态查询工具，通过任务 ID 检索并展示处理任务信息。
 *   挂载时从 URL 查询参数中读取 `jobId` 以支持深度链接。
 *   显示任务状态（彩色标签）、圆形进度指示器，
 *   以及统计信息和完整结果的 JSON 预览。
 *
 * Status types / 状态类型映射:
 *   completed -> success (green) / 完成 -> 成功（绿色）
 *   processing -> warning (amber) / 处理中 -> 警告（琥珀色）
 *   pending    -> info (blue)     / 待处理 -> 信息（蓝色）
 *   failed     -> error (red)     / 失败 -> 错误（红色）
 */
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useMessage } from 'naive-ui'
import { SearchOutline, DocumentTextOutline } from '@vicons/ionicons5'
import { getJobStatus } from '@/api/services'

const { t } = useI18n()
const route = useRoute()
const message = useMessage()

// ---- Reactive State / 响应式状态 ----

/**
 * Job ID from either the URL query param or user input.
 * Initialized from route.query.jobId to support direct links and auto-check on mount.
 * 任务 ID，来自 URL 查询参数或用户输入。
 * 从 route.query.jobId 初始化以支持直接链接访问和挂载时自动查询。
 */
const jobId = ref((route.query.jobId as string) || '')

/** Whether a status check request is in progress / 状态查询请求是否进行中 */
const checking = ref(false)

/** The full job status response from the API / 从 API 获取的完整任务状态响应 */
const statusData = ref<any>(null)

// ---- Functions / 函数 ----

/**
 * Map a job status string to a naive-ui tag type for color coding.
 * 将任务状态字符串映射到 naive-ui 标签类型以实现颜色编码。
 */
const getStatusType = (s: string) =>
  ({ completed: 'success', processing: 'warning', pending: 'info', failed: 'error' } as any)[s] || 'default'

/**
 * Translate a status string using i18n, falling back to the raw string.
 * 使用 i18n 翻译状态字符串，找不到时返回原始字符串。
 */
const getStatusText = (s: string) => t(`status.${s}`) || s

/**
 * Fetch job status from the API by the current jobId.
 * 通过当前的 jobId 从 API 获取任务状态。
 */
const checkStatus = async () => {
  if (!jobId.value.trim()) { message.warning(t('status.job_id_help')); return }
  checking.value = true
  try {
    statusData.value = await getJobStatus(jobId.value)
    message.success('查询成功')
  } catch {
    message.error(t('status.fetch_error'))
    statusData.value = null
  } finally { checking.value = false }
}

// ---- Lifecycle / 生命周期 ----

/**
 * Auto-check status on mount if a jobId was provided via the URL query parameter.
 * 如果在 URL 查询参数中提供了 jobId，则在挂载时自动查询状态。
 */
onMounted(() => { if (jobId.value) checkStatus() })
</script>

<style lang="scss" scoped>
.status-page {
  padding: 28px 40px; min-height: calc(100vh - 64px); position: relative;

  .page-bg {
    position: fixed; inset: 0;
    background: radial-gradient(ellipse at 20% 20%, rgba(245,158,11,0.05) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(251,191,36,0.05) 0%, transparent 50%);
    pointer-events: none; z-index: 0;
  }

  > * { position: relative; z-index: 1; }
}

.status-header {
  margin-bottom: 24px; padding: 24px 32px;

  .status-title { font-size: 32px; font-weight: 800; margin: 0 0 6px; }
  .status-subtitle { font-size: 14px; color: var(--color-text-muted); margin: 0; }
}

.gradient-text-amber {
  background: linear-gradient(135deg, #f59e0b, #d97706, #fbbf24);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.status-card { :deep(.n-card__content) { padding: 24px; } }

.status-item {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 18px; border-radius: var(--radius-lg);
  background: rgba(248,250,252,0.6);

  .si-label { font-weight: 600; font-size: 14px; color: var(--color-text); }
}

.status-dot {
  width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 2px;
  &.completed { background: #10b981; }
  &.processing { background: #f59e0b; animation: pulse 1.5s ease-in-out infinite; }
  &.failed { background: #ef4444; }
  &.pending { background: #3b82f6; }
}

.status-result {
  :deep(.n-code) { border-radius: var(--radius-lg); background: linear-gradient(135deg, rgba(15,23,42,0.98), rgba(30,41,59,0.98)); padding: 18px; }
  :deep(.n-card) { margin-bottom: 16px; &:last-child { margin-bottom: 0; } }
}

:deep(.n-button--primary-type) { box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3); }

.fade-up-enter-active { transition: all 0.5s ease-out; }
.fade-up-leave-active { transition: all 0.2s ease-in; }
.fade-up-enter-from { opacity: 0; transform: translateY(30px); }
.fade-up-leave-to { opacity: 0; }

@keyframes pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(245,158,11,0.4); } 50% { box-shadow: 0 0 0 6px rgba(245,158,11,0); } }
</style>
