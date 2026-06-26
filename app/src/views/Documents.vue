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
        <div v-if="canPreview" class="preview-container">
          <iframe :src="previewUrl" class="preview-frame" title="预览" />
        </div>
        <div v-else class="empty-msg">当前文件类型暂不支持在线预览</div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, NButton, NTag, NIcon } from 'naive-ui'
import { RefreshOutline, CloudUploadOutline, DocumentTextOutline, CheckmarkCircleOutline, HourglassOutline } from '@vicons/ionicons5'
import { listDocuments, getDocumentDetail, getDocumentFileUrl, type DocumentListResponse, type DocumentDetail } from '@/api/services'

const router = useRouter()
const message = useMessage()

const loading = ref(false)
const documents = ref<DocumentListResponse['documents']>([])
const pagination = ref({ page: 1, pageSize: 20, pageCount: 1, prefix: (info: any) => `共 ${info.itemCount} 条`, onChange: (p: number) => { pagination.value.page = p; loadDocuments() } })
const sortBy = ref<'created_at' | 'filename'>('created_at')
const showDetailModal = ref(false)
const selectedDocument = ref<any>(null)
const documentDetail = ref<DocumentDetail | null>(null)
const previewUrl = computed(() => selectedDocument.value ? getDocumentFileUrl(selectedDocument.value.id) : '')
const canPreview = computed(() => documentDetail.value && (documentDetail.value.mime?.includes('pdf') || documentDetail.value.kind === 'pdf'))

const totalDocuments = computed(() => documents.value.length)
const completedDocuments = computed(() => documents.value.filter(d => d.processing_status === 'completed').length)
const pendingDocuments = computed(() => documents.value.filter(d => d.processing_status === 'uploaded').length)

const statCards = computed(() => [
  { label: '总文档数', value: totalDocuments.value, icon: DocumentTextOutline, bg: 'linear-gradient(135deg, #3b82f6, #1e40af)' },
  { label: '已处理', value: completedDocuments.value, icon: CheckmarkCircleOutline, bg: 'linear-gradient(135deg, #10b981, #059669)' },
  { label: '待处理', value: pendingDocuments.value, icon: HourglassOutline, bg: 'linear-gradient(135deg, #f59e0b, #d97706)' }
])

const docStats = computed(() => {
  const s = documentDetail.value?.statistics
  return s ? [
    { label: '文本块', value: s.chunk_count },
    { label: '概念节点', value: s.concept_count },
    { label: '论断', value: s.claim_count },
    { label: '关系', value: s.relation_count }
  ] : []
})

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

const formatFileSize = (b: number) => { if (!b) return '0 B'; const k = 1024; const sizes = ['B','KB','MB','GB']; const i = Math.floor(Math.log(b) / Math.log(k)); return Math.round(b / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i] }
const formatTime = (t: string | null) => !t ? '未知' : new Date(t).toLocaleString('zh-CN')
const getKindColor = (k: string) => ({ pdf: 'error', md: 'info', txt: 'warning', word: 'success' } as any)[k] || 'default'

const handleViewDocument = async (doc: any) => {
  selectedDocument.value = doc; showDetailModal.value = true
  try { documentDetail.value = await getDocumentDetail(doc.id) } catch (e: any) { message.error('加载详情失败') }
}

const columns = [
  { title: '文件名', key: 'filename', width: 250, ellipsis: { tooltip: true } },
  { title: '类型', key: 'kind', width: 80, render: (r: any) => h(NTag, { type: getKindColor(r.kind) }, () => r.kind?.toUpperCase()) },
  { title: '大小', key: 'size', width: 100, render: (r: any) => formatFileSize(r.size) },
  { title: '文本块', key: 'chunk_count', width: 80, align: 'center' as const, render: (r: any) => h('span', { style: 'font-weight:700;color:#3b82f6' }, r.chunk_count) },
  { title: '概念', key: 'concept_count', width: 80, align: 'center' as const, render: (r: any) => h('span', { style: 'font-weight:700;color:#10b981' }, r.concept_count) },
  { title: '状态', key: 'processing_status', width: 90, render: (r: any) => h(NTag, { type: r.processing_status === 'completed' ? 'success' : 'warning' }, () => r.processing_status === 'completed' ? '已完成' : '待处理') },
  { title: '上传时间', key: 'created_at', width: 170, render: (r: any) => formatTime(r.created_at) },
  { title: '操作', key: 'actions', width: 200, fixed: 'right' as const, render: (r: any) => h('div', { style: 'display:flex;gap:8px' }, [
    h(NButton, { size: 'small', type: 'primary', text: true, onClick: () => handleViewDocument(r) }, () => '查看'),
    h(NButton, { size: 'small', type: 'info', text: true, onClick: () => router.push(`/graph?doc_id=${r.id}`) }, () => '图谱')
  ]) }
]

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
  .preview-container { margin-top: 12px; border: 1px solid var(--color-border); border-radius: var(--radius-lg); overflow: hidden; }
  .preview-frame { width: 100%; height: 600px; border: none; background: #fff; }
  .empty-msg { padding: 24px; text-align: center; color: var(--color-text-muted); }
}
</style>
