<template>
  <div class="documents-page">
    <div class="page-bg"></div>

    <!-- Header -->
    <div class="page-header glass-card">
      <div class="header-content">
        <h1 class="page-title gradient-text-blue">文档管理</h1>
        <p class="page-subtitle">查看和管理已上传的文档 · Document Management</p>
      </div>
      <div class="header-actions">
        <n-button type="primary" @click="loadDocuments" :loading="loading">
          <template #icon><n-icon><refresh-outline /></n-icon></template>
          刷新
        </n-button>
        <n-button @click="$router.push('/knowledge')">
          <template #icon><n-icon><cloud-upload-outline /></n-icon></template>
          上传文档
        </n-button>
      </div>
    </div>

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card" v-for="s in statCards" :key="s.label">
        <div class="stat-icon" :style="{ background: s.bg }">
          <n-icon size="28"><component :is="s.icon" /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">{{ s.label }}</div>
          <div class="stat-value count-up">{{ s.value }}</div>
        </div>
      </div>
    </div>

    <!-- Documents Table -->
    <n-card class="documents-card glass-card" :bordered="false">
      <template #header>
        <div class="card-header">
          <h3>所有文档</h3>
          <n-select v-model:value="sortBy" :options="[{ label: '最新上传', value: 'created_at' }, { label: '文件名', value: 'filename' }]" style="width: 150px" @update:value="loadDocuments" />
        </div>
      </template>

      <n-spin :show="loading">
        <div v-if="documents.length === 0" class="empty-state">
          <n-empty description="暂无文档">
            <template #extra>
              <n-button type="primary" @click="$router.push('/knowledge')">上传第一个文档</n-button>
            </template>
          </n-empty>
        </div>

        <n-data-table v-else :columns="columns" :data="documents" :pagination="pagination" :scroll-x="1200" striped />
      </n-spin>
    </n-card>

    <!-- Detail Modal -->
    <n-modal v-model:show="showDetailModal" preset="dialog" :title="`文档详情 — ${selectedDocument?.filename || ''}`" style="width: 85%; max-width: 1000px" :mask-closable="false">
      <div v-if="selectedDocument && documentDetail" class="document-detail">
        <n-divider>基本信息</n-divider>
        <n-grid :cols="2" :x-gap="24" :y-gap="12">
          <n-gi><div class="info-item"><span class="label">文件名:</span><span class="value">{{ documentDetail.filename }}</span></div></n-gi>
          <n-gi><div class="info-item"><span class="label">类型:</span><n-tag :type="getKindColor(documentDetail.kind)">{{ documentDetail.kind?.toUpperCase() }}</n-tag></div></n-gi>
          <n-gi><div class="info-item"><span class="label">大小:</span><span class="value">{{ formatFileSize(documentDetail.size) }}</span></div></n-gi>
          <n-gi><div class="info-item"><span class="label">状态:</span><n-tag :type="documentDetail.processing_status === 'completed' ? 'success' : 'warning'">{{ documentDetail.processing_status === 'completed' ? '已完成' : '待处理' }}</n-tag></div></n-gi>
          <n-gi><div class="info-item"><span class="label">上传时间:</span><span class="value">{{ formatTime(documentDetail.created_at) }}</span></div></n-gi>
          <n-gi><div class="info-item"><span class="label">更新时间:</span><span class="value">{{ formatTime(documentDetail.updated_at) }}</span></div></n-gi>
        </n-grid>

        <n-divider>处理统计</n-divider>
        <n-grid :cols="4" :x-gap="16">
          <n-gi v-for="st in docStats" :key="st.label"><div class="stat-box"><div class="sv">{{ st.value }}</div><div class="sl">{{ st.label }}</div></div></n-gi>
        </n-grid>

        <n-divider v-if="documentDetail.themes?.length">关联主题</n-divider>
        <div v-if="documentDetail.themes?.length">
          <n-space vertical :size="12">
            <div v-for="theme in documentDetail.themes" :key="theme.id" class="theme-item">
              <n-card :bordered="false" size="small">
                <div class="theme-header">
                  <n-tag :type="theme.level === 1 ? 'success' : 'info'" size="small">Level {{ theme.level }}</n-tag>
                  <span class="theme-label">{{ theme.label }}</span>
                  <span class="theme-count">{{ theme.member_count }} 成员</span>
                </div>
                <p class="theme-summary">{{ theme.summary }}</p>
              </n-card>
            </div>
          </n-space>
        </div>

        <n-divider>文档预览</n-divider>
        <!-- PDF Preview: 使用 iframe 直接嵌入 PDF URL -->
        <!-- PDF Preview: Embed PDF via iframe with browser-native viewer -->
        <div v-if="isPDF" class="preview-container">
          <iframe :src="previewUrl" class="preview-frame" title="预览" />
        </div>
        <!-- Markdown Preview: 使用 marked 库渲染为 HTML -->
        <!-- Markdown Preview: Render via marked library into styled HTML -->
        <div v-else-if="isMarkdown" class="preview-container">
          <n-spin :show="previewLoading" />
          <div v-if="!previewLoading && previewContent" class="markdown-body" v-html="previewContent"></div>
          <div v-else-if="!previewLoading && previewError" class="empty-msg">{{ previewError }}</div>
        </div>
        <!-- TXT Preview: 纯文本以 <pre> 展示，保留空白格式 -->
        <!-- TXT Preview: Render plain text inside <pre> to preserve whitespace -->
        <div v-else-if="isTXT" class="preview-container">
          <n-spin :show="previewLoading" />
          <pre v-if="!previewLoading && previewContent" class="txt-body">{{ previewContent }}</pre>
          <div v-else-if="!previewLoading && previewError" class="empty-msg">{{ previewError }}</div>
        </div>
        <!-- Word Preview: 尝试 iframe，附下载备用链接 -->
        <!-- Word Preview: Attempt iframe rendering with a download fallback link -->
        <div v-else-if="isWord" class="preview-container">
          <iframe :src="previewUrl" class="preview-frame" title="预览" />
          <div class="preview-note">💡 如无法在线预览 Word 文档，可<a :href="previewUrl" download>点击下载</a>后查看</div>
        </div>
        <!-- Unsupported -->
        <div v-else class="empty-msg">当前文件类型暂不支持在线预览</div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
/**
 * Documents.vue - 文档管理视图 / Document Management View
 *
 * 【功能 / Functionality】
 * 1. 文档列表展示（支持分页和排序）/ Document list with pagination and sorting
 * 2. 文档详情弹窗 / Document detail modal
 * 3. 文档预览（PDF 内嵌 iframe, Markdown 使用 marked 渲染, TXT 纯文本, Word 内嵌）
 *    / Document preview (PDF via iframe, Markdown via marked, TXT plain text, Word via iframe)
 * 4. 文档删除（带级联清理确认）/ Document deletion with cascade cleanup confirmation
 * 5. 跳转到对应文档的图谱视图 / Navigation to document-specific graph view
 *
 * 【角色 / Role】
 * 文档管理的核心视图，提供文档的 CRUD（仅 D 和 R）操作入口和在线预览功能。
 * Core view for document management, providing read/delete operations and online preview.
 */

import { ref, computed, h } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, useDialog, NButton, NTag, NIcon, NSpin } from 'naive-ui'
import { RefreshOutline, CloudUploadOutline, DocumentTextOutline, CheckmarkCircleOutline, HourglassOutline } from '@vicons/ionicons5'
import { listDocuments, getDocumentDetail, getDocumentFileUrl, deleteDocument, API_BASE, type DocumentListResponse, type DocumentDetail } from '@/api/services'
import { marked } from 'marked'

const router = useRouter()
const message = useMessage()
const dialog = useDialog()

// ---------------------------------------------------------------------------
// 响应式状态 / Reactive State
// ---------------------------------------------------------------------------

/** 数据加载状态 / Data loading state (for spin and disabled buttons) */
const loading = ref(false)

/** 文档列表数据 / Document list from the API */
const documents = ref<DocumentListResponse['documents']>([])

/**
 * 分页配置 / Pagination configuration
 * - page: 当前页码 / Current page number
 * - pageSize: 每页条数 / Items per page
 * - pageCount: 总页数 / Total pages (computed from API response)
 * - prefix: 分页器前缀文本 / Paginator prefix text
 * - onChange: 页码变更回调，自动重新加载 / Page change callback triggering reload
 */
const pagination = ref({
  page: 1,
  pageSize: 20,
  pageCount: 1,
  prefix: (info: any) => `共 ${info.itemCount} 条`,
  onChange: (p: number) => { pagination.value.page = p; loadDocuments() }
})

/** 排序字段 / Sort field for document listing */
const sortBy = ref<'created_at' | 'filename'>('created_at')

/** 控制详情弹窗显示 / Controls detail modal visibility */
const showDetailModal = ref(false)

/** 当前选中的文档（从表格行点击） / Currently selected document row */
const selectedDocument = ref<any>(null)

/** 完整的文档详情数据 / Full document detail from API */
const documentDetail = ref<DocumentDetail | null>(null)

/**
 * 文档预览 URL（计算属性）
 * 根据选中文档的 ID 动态生成文件访问 URL。
 * Computed preview URL derived from the selected document's ID.
 */
const previewUrl = computed(() => selectedDocument.value ? getDocumentFileUrl(selectedDocument.value.id) : '')

// ---------------------------------------------------------------------------
// 非 PDF 格式的预览状态 / Preview state for non-PDF formats
// (PDF 直接通过 iframe + URL 渲染，无需额外加载)
// (PDF is rendered directly via iframe+URL, no extra loading needed)
// ---------------------------------------------------------------------------

/** 文本预览内容加载中 / Text preview content loading */
const previewLoading = ref(false)

/** 已渲染的文本预览内容 / Rendered text preview content */
const previewContent = ref('')

/** 预览错误信息 / Preview error message */
const previewError = ref('')

// ---------------------------------------------------------------------------
// 文档类型辅助计算属性 / Document Type Helper Computed Properties
// ---------------------------------------------------------------------------

/** 文档类型的小写形式 / Lowercased document kind for type checking */
const docKind = computed(() => documentDetail.value?.kind?.toLowerCase() || '')
const isPDF = computed(() => docKind.value === 'pdf')
const isMarkdown = computed(() => docKind.value === 'md' || docKind.value === 'markdown')
const isTXT = computed(() => docKind.value === 'txt')
const isWord = computed(() => docKind.value === 'word' || docKind.value === 'doc' || docKind.value === 'docx')
const canPreview = computed(() => isPDF.value || isMarkdown.value || isTXT.value || isWord.value)

// ---------------------------------------------------------------------------
// 统计计算属性 / Stats Computed Properties
// ---------------------------------------------------------------------------

/** 总文档数 / Total document count */
const totalDocuments = computed(() => documents.value.length)

/** 已完成处理的文档数 / Completed processing count */
const completedDocuments = computed(() => documents.value.filter(d => d.processing_status === 'completed').length)

/** 待处理文档数 / Pending processing count */
const pendingDocuments = computed(() => documents.value.filter(d => d.processing_status === 'uploaded').length)

/** 顶部统计卡片配置 / Top stats card configuration */
const statCards = computed(() => [
  { label: '总文档数', value: totalDocuments.value, icon: DocumentTextOutline, bg: 'linear-gradient(135deg, #3b82f6, #1e40af)' },
  { label: '已处理', value: completedDocuments.value, icon: CheckmarkCircleOutline, bg: 'linear-gradient(135deg, #10b981, #059669)' },
  { label: '待处理', value: pendingDocuments.value, icon: HourglassOutline, bg: 'linear-gradient(135deg, #f59e0b, #d97706)' }
])

/** 文档处理统计明细（文本块、概念、论断、关系数） / Document processing statistics detail */
const docStats = computed(() => {
  const s = documentDetail.value?.statistics
  return s ? [
    { label: '文本块', value: s.chunk_count },
    { label: '概念节点', value: s.concept_count },
    { label: '论断', value: s.claim_count },
    { label: '关系', value: s.relation_count }
  ] : []
})

// ---------------------------------------------------------------------------
// 数据加载 / Data Loading
// ---------------------------------------------------------------------------

/**
 * 加载文档列表 / Load document list from API
 *
 * 使用分页参数和排序字段请求文档列表，并更新 pageCount。
 * Requests the document list with pagination and sort parameters, updating pageCount.
 * skip = (page - 1) * pageSize 实现分页偏移。
 * skip = (page - 1) * pageSize implements pagination offset.
 */
const loadDocuments = async () => {
  loading.value = true
  try {
    const skip = (pagination.value.page - 1) * pagination.value.pageSize
    const r = await listDocuments(skip, pagination.value.pageSize, sortBy.value)
    documents.value = r.documents
    pagination.value.pageCount = Math.ceil(r.total / pagination.value.pageSize)
  } catch (e: any) { message.error('加载失败: ' + e.message) }
  finally { loading.value = false }
}

// ---------------------------------------------------------------------------
// 工具函数 / Utility Functions
// ---------------------------------------------------------------------------

/**
 * 格式化文件大小 / Format file size to human-readable string
 * @param b - 文件字节数 / File size in bytes
 * @returns 格式化后的字符串，如 "1.23 MB" / Formatted string like "1.23 MB"
 */
const formatFileSize = (b: number) => {
  if (!b) return '0 B'
  const k = 1024
  const sizes = ['B','KB','MB','GB']
  const i = Math.floor(Math.log(b) / Math.log(k))
  return Math.round(b / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

/**
 * 格式化时间戳 / Format timestamp to localized string
 * @param t - ISO 时间字符串或 null / ISO time string or null
 * @returns "YYYY/MM/DD HH:mm:ss" 格式或 "未知" / Formatted string or "未知"
 */
const formatTime = (t: string | null) => !t ? '未知' : new Date(t).toLocaleString('zh-CN')

/**
 * 获取文档类型对应的 Naive UI Tag 颜色 / Get tag color for document kind
 * @param k - 文档类型标识 / Document kind identifier
 * @returns Naive UI tag type ('error' | 'info' | 'warning' | 'success')
 */
const getKindColor = (k: string) => ({ pdf: 'error', md: 'info', txt: 'warning', word: 'success' } as any)[k] || 'default'

// ---------------------------------------------------------------------------
// 文档操作 / Document Operations
// ---------------------------------------------------------------------------

/**
 * 查看文档详情 / View document detail in modal
 *
 * 1. 设置选中文档并显示弹窗 / Set selected document and show modal
 * 2. 重置预览状态 / Reset preview state
 * 3. 调用 API 获取完整详情 / Fetch full detail from API
 * 4. 对 Markdown 和 TXT 类型额外加载文本预览内容 / For MD/TXT, also load text content
 * @param doc - 文档对象（来自表格行） / Document object from table row
 */
const handleViewDocument = async (doc: any) => {
  selectedDocument.value = doc
  showDetailModal.value = true
  // 重置预览状态 / Reset preview loading/error/content
  previewLoading.value = false
  previewContent.value = ''
  previewError.value = ''
  try {
    documentDetail.value = await getDocumentDetail(doc.id)
    // 对 Markdown 和 TXT 类型，额外拉取文件内容用于客户端渲染
    // For Markdown and TXT, fetch raw file content for client-side rendering
    const kind = documentDetail.value?.kind?.toLowerCase()
    if (kind === 'md' || kind === 'markdown' || kind === 'txt') {
      await loadTextPreview(doc.id, kind)
    }
  } catch (e: any) { message.error('加载详情失败') }
}

/**
 * 加载文本类文档的预览内容 / Load text-based document preview content
 *
 * 对 Markdown 使用 marked.parse() 渲染为 HTML，TXT 直接保留纯文本。
 * For Markdown, uses marked.parse() to render HTML; for TXT, keeps plain text.
 *
 * @param docId - 文档 ID / Document ID
 * @param kind - 文档类型 / Document kind ('md' | 'markdown' | 'txt')
 */
const loadTextPreview = async (docId: string, kind: string) => {
  previewLoading.value = true
  previewError.value = ''
  previewContent.value = ''
  try {
    // 从 uploads 目录获取原始文件 / Fetch raw file from uploads directory
    const url = `${API_BASE}/uploads/${docId}/file`
    const response = await fetch(url)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const text = await response.text()
    if (kind === 'md' || kind === 'markdown') {
      // Markdown: 使用 marked 库异步解析为 HTML
      // Use marked library to asynchronously parse Markdown into HTML
      previewContent.value = await marked.parse(text)
    } else {
      // TXT: 直接展示纯文本 / Display plain text directly
      previewContent.value = text
    }
  } catch (e: any) {
    previewError.value = '预览加载失败: ' + (e.message || '未知错误')
  } finally {
    previewLoading.value = false
  }
}

/**
 * 删除文档（带级联清理确认对话框） / Delete document with cascade cleanup confirmation
 *
 * 调用 deleteDocument API 会级联删除：
 * - 上传目录中的原始文件 / Original file in upload directory
 * - 文档对应的图谱节点及所有关联边 / Graph nodes and edges for this document
 * - 被孤立（无边连接）的节点 / Orphan nodes left with no edges
 *
 * @param doc - 待删除的文档对象 / Document to delete
 */
const handleDeleteDocument = (doc: any) => {
  dialog.warning({
    title: '确认删除',
    // 警告内容说明级联删除的范围 / Warning explaining cascade deletion scope
    content: `确定要删除文档 "${doc.filename}" 吗？此操作将同时删除：\n• 上传目录中的原始文件\n• 该文档的图谱节点及所有关联边\n• 被孤立（无边连接）的节点\n\n此操作不可撤销！`,
    positiveText: '确认删除',
    negativeText: '取消',
    positiveButtonProps: { type: 'error' as const },
    onPositiveClick: async () => {
      try {
        const result = await deleteDocument(doc.id)
        // 成功后显示详细清理结果 / Show detailed cleanup results after success
        message.success(
          `已删除 "${result.filename}"：文件${result.file_deleted ? '已' : '未'}删除，` +
          `${result.edges_deleted} 条边、${result.orphan_nodes_deleted} 个孤立节点已清理`
        )
        await loadDocuments()
      } catch (e: any) {
        // 尝试提取后端返回的错误详情 / Attempt to extract backend error detail
        const errMsg = e?.response?.data?.detail || e?.message || '未知错误'
        message.error('删除失败: ' + errMsg)
      }
    }
  })
}

// ---------------------------------------------------------------------------
// 表格列定义 / DataTable Column Definitions
// ---------------------------------------------------------------------------

/**
 * 文档列表的表格列配置
 * Columns for the document list data table.
 * 使用 Naive UI 的 h() 渲染函数实现自定义操作按钮列。
 * Uses Naive UI's h() render function for custom action button column.
 */
const columns = [
  { title: '文件名', key: 'filename', width: 250, ellipsis: { tooltip: true } },
  { title: '类型', key: 'kind', width: 80, render: (r: any) => h(NTag, { type: getKindColor(r.kind) }, () => r.kind?.toUpperCase()) },
  { title: '大小', key: 'size', width: 100, render: (r: any) => formatFileSize(r.size) },
  { title: '文本块', key: 'chunk_count', width: 80, align: 'center' as const, render: (r: any) => h('span', { style: 'font-weight:700;color:#3b82f6' }, r.chunk_count) },
  { title: '概念', key: 'concept_count', width: 80, align: 'center' as const, render: (r: any) => h('span', { style: 'font-weight:700;color:#10b981' }, r.concept_count) },
  { title: '状态', key: 'processing_status', width: 90, render: (r: any) => h(NTag, { type: r.processing_status === 'completed' ? 'success' : 'warning' }, () => r.processing_status === 'completed' ? '已完成' : '待处理') },
  { title: '上传时间', key: 'created_at', width: 170, render: (r: any) => formatTime(r.created_at) },
  { // 操作列：固定在右侧，包含 查看 / 图谱 / 删除 三个按钮
    title: '操作', key: 'actions', width: 260, fixed: 'right' as const,
    render: (r: any) => h('div', { style: 'display:flex;gap:8px' }, [
      h(NButton, { size: 'small', type: 'primary', text: true, onClick: () => handleViewDocument(r) }, () => '查看'),
      h(NButton, { size: 'small', type: 'info', text: true, onClick: () => router.push(`/graph?doc_id=${r.id}`) }, () => '图谱'),
      h(NButton, { size: 'small', type: 'error', text: true, onClick: () => handleDeleteDocument(r) }, () => '删除')
    ])
  }
]

// ---------------------------------------------------------------------------
// 启动加载 / Initial Load
// ---------------------------------------------------------------------------

/** 组件初始化时立即加载文档列表 / Load document list on component initialization */
loadDocuments()
</script>

<style lang="scss" scoped>
.documents-page {
  padding: 28px 40px; min-height: calc(100vh - 64px); position: relative;

  .page-bg {
    position: fixed; inset: 0;
    background: radial-gradient(ellipse at 20% 20%, rgba(59,130,246,0.05) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(96,165,250,0.05) 0%, transparent 50%);
    pointer-events: none; z-index: 0;
  }

  > * { position: relative; z-index: 1; }
}

.page-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 24px; padding: 24px 32px;

  .page-title { font-size: 30px; font-weight: 800; margin: 0 0 6px; }
  .page-subtitle { font-size: 14px; color: var(--color-text-muted); margin: 0; }
  .header-actions { display: flex; gap: 10px; }
}

.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin-bottom: 24px; }

.stat-card {
  display: flex; gap: 16px; padding: 20px;
  background: var(--color-surface); border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm); border: 1px solid var(--color-border-light);
  transition: all var(--transition-base);

  &:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }

  .stat-icon { width: 54px; height: 54px; border-radius: var(--radius-lg); display: flex; align-items: center; justify-content: center; color: #fff; flex-shrink: 0; }
  .stat-content { flex: 1; .stat-label { font-size: 12px; color: var(--color-text-muted); margin-bottom: 6px; } .stat-value { font-size: 24px; font-weight: 800; color: var(--color-text); } }
}

.documents-card {
  .card-header { display: flex; justify-content: space-between; align-items: center; h3 { margin: 0; font-weight: 700; } }
}

.empty-state { padding: 60px 20px; text-align: center; }

.document-detail {
  padding: 8px 0;
  .info-item { display: flex; gap: 12px; align-items: center; .label { font-weight: 600; color: var(--color-text-secondary); min-width: 80px; } }
  .stat-box { padding: 18px; border-radius: var(--radius-lg); background: var(--color-bg-alt); text-align: center; .sv { font-size: 26px; font-weight: 800; color: #3b82f6; } .sl { font-size: 12px; color: var(--color-text-muted); margin-top: 6px; } }
  .theme-header { display: flex; align-items: center; gap: 12px; .theme-label { font-weight: 600; flex: 1; } .theme-count { font-size: 13px; color: var(--color-text-muted); } }
  .theme-summary { margin: 8px 0 0; color: var(--color-text-secondary); line-height: 1.5; }
  .preview-container { margin-top: 12px; border: 1px solid var(--color-border); border-radius: var(--radius-lg); overflow: hidden; position: relative; min-height: 200px; }
  .preview-frame { width: 100%; height: 600px; border: none; background: #fff; }
  .empty-msg { padding: 24px; text-align: center; color: var(--color-text-muted); }
  .markdown-body {
    padding: 24px 28px; max-height: 600px; overflow-y: auto; background: #fff; color: #1f2937; line-height: 1.75; font-size: 15px;
    h1 { font-size: 1.8em; font-weight: 700; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; margin: 24px 0 16px; }
    h2 { font-size: 1.5em; font-weight: 700; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin: 20px 0 12px; }
    h3 { font-size: 1.25em; font-weight: 600; margin: 16px 0 10px; }
    p { margin: 8px 0; }
    ul, ol { padding-left: 24px; margin: 8px 0; li { margin: 4px 0; } }
    code { background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; font-family: 'Fira Code', monospace; }
    pre { background: #1f2937; color: #e5e7eb; padding: 16px 20px; border-radius: 8px; overflow-x: auto; margin: 12px 0;
      code { background: none; padding: 0; color: inherit; }
    }
    blockquote { border-left: 4px solid #3b82f6; padding: 8px 16px; margin: 12px 0; background: #f0f7ff; color: #374151; }
    table { border-collapse: collapse; width: 100%; margin: 12px 0;
      th, td { border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; }
      th { background: #f9fafb; font-weight: 600; }
    }
    a { color: #3b82f6; text-decoration: underline;
      &:hover { color: #2563eb; }
    }
    strong { font-weight: 700; color: #111827; }
    hr { border: none; border-top: 1px solid #e5e7eb; margin: 20px 0; }
  }
  .txt-body {
    padding: 20px 24px; max-height: 600px; overflow-y: auto; background: #fafbfc; color: #1f2937;
    font-family: 'Fira Code', 'Cascadia Code', 'Consolas', monospace; font-size: 14px; line-height: 1.7;
    white-space: pre-wrap; word-break: break-word; margin: 0; border: none;
  }
  .preview-note { padding: 10px 16px; background: #fef3c7; color: #92400e; font-size: 13px; border-top: 1px solid #fcd34d;
    a { color: #3b82f6; font-weight: 600; }
  }
}
</style>
