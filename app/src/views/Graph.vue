<template>
  <div class="graph-page">
    <div class="page-bg"></div>

    <!-- Header -->
    <div class="graph-header glass-card">
      <div>
        <h1 class="graph-title gradient-text-green">{{ t('graph.title') }}</h1>
        <p class="graph-subtitle">交互式知识图谱可视化 · Interactive Knowledge Graph</p>
      </div>
    </div>

    <n-card class="graph-card glass-card" :bordered="false">
      <!-- Control Panel -->
      <div class="control-panel">
        <n-space :size="12" align="center" wrap>
          <!-- Search nodes -->
          <div class="control-item">
            <n-input
              v-model:value="searchQuery"
              round
              clearable
              placeholder="搜索节点..."
              style="width: 200px"
              @update:value="handleSearch"
            >
              <template #prefix><n-icon :component="SearchOutline" /></template>
            </n-input>
          </div>

          <!-- Node Limit -->
          <div class="control-item">
            <n-input-number v-model:value="nodeLimit" :min="10" :max="1000" :step="10" style="width: 140px">
              <template #prefix>节点:</template>
            </n-input-number>
          </div>

          <!-- Layout Type -->
          <div class="control-item">
            <n-select v-model:value="layoutType" :options="layoutOptions" style="width: 130px" @update:value="handleLayoutChange" />
          </div>

          <!-- Load Button -->
          <n-button type="primary" :loading="loading" @click="loadGraph" size="medium">
            <template #icon><n-icon><refresh-outline /></n-icon></template>
            加载图谱
          </n-button>

          <!-- Document filter -->
          <div class="control-item">
            <n-select
              v-model:value="currentDocumentId"
              :options="documentOptions"
              placeholder="筛选文档..."
              clearable
              filterable
              style="width: 200px"
              @update:value="handleDocumentChange"
            />
            <n-input-number
              v-if="currentDocumentId"
              v-model:value="documentDepth"
              :min="1" :max="5" :step="1"
              size="small"
              style="width: 100px"
            >
              <template #prefix>深度</template>
            </n-input-number>
            <n-button v-if="currentDocumentId" size="small" tertiary @click="resetDocumentFilter">查看全部</n-button>
          </div>

          <n-divider vertical />

          <!-- CRUD buttons -->
          <n-button-group>
            <n-button type="success" @click="handleCreateNode" :disabled="!cy">
              <template #icon><n-icon><add-outline /></n-icon></template>
              创建节点
            </n-button>
            <n-button @click="handleCreateEdge" :disabled="!cy">
              <template #icon><n-icon><link-outline /></n-icon></template>
              创建关系
            </n-button>
          </n-button-group>

          <n-divider vertical />

          <!-- View controls -->
          <n-button-group>
            <n-button @click="zoomIn" :disabled="!cy">
              <template #icon><n-icon><add-outline /></n-icon></template>
            </n-button>
            <n-button @click="zoomOut" :disabled="!cy">
              <template #icon><n-icon><remove-outline /></n-icon></template>
            </n-button>
            <n-button @click="fitView" :disabled="!cy">
              <template #icon><n-icon><expand-outline /></n-icon></template>
            </n-button>
            <n-button @click="resetView" :disabled="!cy">
              <template #icon><n-icon><contract-outline /></n-icon></template>
            </n-button>
          </n-button-group>

          <!-- Export -->
          <n-button @click="exportGraph" :disabled="!cy">
            <template #icon><n-icon><download-outline /></n-icon></template>
            导出
          </n-button>
        </n-space>
      </div>

      <!-- Stats Bar -->
      <div v-if="graphData" class="stats-bar">
        <div class="stat-item stat-blue">
          <n-icon size="18"><cube-outline /></n-icon>
          <span class="stat-label">节点</span>
          <n-number-animation :from="0" :to="graphData.nodes.length" :duration="1200" class="stat-value" />
        </div>
        <div class="stat-item stat-green">
          <n-icon size="18"><git-network-outline /></n-icon>
          <span class="stat-label">关系</span>
          <n-number-animation :from="0" :to="graphData.edges.length" :duration="1200" class="stat-value" />
        </div>
        <div class="stat-item stat-yellow" v-if="currentDocumentId">
          <n-icon size="18"><information-circle-outline /></n-icon>
          <span class="stat-label">文本块</span>
          <span class="stat-value">{{ chunkCount }}</span>
        </div>
        <div class="stat-item stat-purple" v-if="selectedNode">
          <n-icon size="18"><information-circle-outline /></n-icon>
          <span class="stat-label">选中</span>
          <span class="stat-value name">{{ selectedNode.label }}</span>
        </div>
      </div>

      <!-- Graph Container -->
      <div class="graph-wrapper">
        <div ref="graphContainer" class="graph-container"></div>

        <!-- Search results overlay -->
        <div v-if="searchResults.length > 0" class="search-results">
          <div v-for="r in searchResults" :key="r.id" class="search-result-item" @click="focusNode(r.id)">
            <n-icon size="14"><cube-outline /></n-icon>
            <span>{{ r.label }}</span>
            <n-tag size="tiny" :bordered="false">{{ r.type }}</n-tag>
          </div>
        </div>

        <!-- Legend -->
        <div class="graph-legend">
          <div class="legend-title">节点类型</div>
          <div class="legend-item" v-for="item in legendItems" :key="item.label">
            <div class="legend-color" :style="{ background: item.color }"></div>
            <span>{{ item.label }}</span>
          </div>
        </div>

        <!-- Loading Overlay -->
        <transition name="fade">
          <div v-if="loading" class="loading-overlay">
            <n-spin size="large">
              <template #description>
                <div class="loading-text">正在加载图谱数据...</div>
              </template>
            </n-spin>
          </div>
        </transition>

        <!-- Empty State -->
        <div v-if="!loading && !graphData" class="empty-state">
          <n-empty description="暂无图谱数据" size="large">
            <template #icon><n-icon size="72" :component="GitNetworkOutline" style="opacity:0.2" /></template>
            <template #extra>
              <n-button type="primary" @click="$router.push('/knowledge')" size="large">去构建知识</n-button>
            </template>
          </n-empty>
        </div>
      </div>

      <!-- Node Detail Drawer -->
      <n-drawer v-model:show="showNodeDetail" :width="420" placement="right">
        <n-drawer-content title="节点详情" closable>
          <div v-if="selectedNode" class="node-detail">
            <n-descriptions :column="1" bordered label-placement="left">
              <n-descriptions-item label="ID"><n-text code>{{ selectedNode.id }}</n-text></n-descriptions-item>
              <n-descriptions-item label="标签"><n-tag type="info" size="small">{{ selectedNode.label }}</n-tag></n-descriptions-item>
              <n-descriptions-item v-for="(value, key) in selectedNode.properties" :key="key" :label="key">
                {{ value }}
              </n-descriptions-item>
            </n-descriptions>
          </div>
        </n-drawer-content>
      </n-drawer>

      <!-- Context Menu -->
      <div v-if="contextMenuVisible" class="context-menu" :style="{ left: contextMenuPosition.x + 'px', top: contextMenuPosition.y + 'px' }">
        <template v-if="contextMenuType === 'node'">
          <div class="context-menu-item" @click="handleEditNode"><n-icon :component="CreateOutline" /><span>编辑节点</span></div>
          <div class="context-menu-item" @click="handleCreateEdge"><n-icon :component="LinkOutline" /><span>创建关系</span></div>
          <n-divider style="margin:4px 0" />
          <div class="context-menu-item danger" @click="handleDeleteNode"><n-icon :component="TrashOutline" /><span>删除节点</span></div>
        </template>
        <template v-if="contextMenuType === 'edge'">
          <div class="context-menu-item danger" @click="handleDeleteEdge"><n-icon :component="TrashOutline" /><span>删除关系</span></div>
        </template>
        <template v-if="contextMenuType === 'canvas'">
          <div class="context-menu-item" @click="handleCreateNode"><n-icon :component="AddOutline" /><span>创建节点</span></div>
          <div class="context-menu-item" @click="handleCreateEdge"><n-icon :component="LinkOutline" /><span>创建关系</span></div>
        </template>
      </div>

      <!-- Modals -->
      <n-modal v-model:show="showNodeEditModal" preset="dialog" title="编辑节点" style="width:600px">
        <n-form :model="nodeEditForm" label-placement="left" label-width="100px">
          <n-form-item label="节点 ID"><n-input :value="nodeEditForm.id" disabled /></n-form-item>
          <n-form-item label="标签"><n-dynamic-tags v-model:value="nodeEditForm.labels" /></n-form-item>
          <n-form-item label="属性">
            <div style="width:100%">
              <div v-for="key in Object.keys(nodeEditForm.properties)" :key="key" style="display:flex;gap:8px;margin-bottom:8px">
                <n-input :value="String(key)" disabled style="width:150px" />
                <n-input v-model:value="nodeEditForm.properties[key]" style="flex:1" />
              </div>
            </div>
          </n-form-item>
        </n-form>
        <template #action><n-space><n-button @click="showNodeEditModal = false">取消</n-button><n-button type="primary" @click="submitNodeEdit">保存</n-button></n-space></template>
      </n-modal>

      <n-modal v-model:show="showNodeCreateModal" preset="dialog" title="创建节点" style="width:600px">
        <n-form :model="nodeCreateForm" label-placement="left" label-width="100px">
          <n-form-item label="标签"><n-dynamic-tags v-model:value="nodeCreateForm.labels" /></n-form-item>
          <n-form-item label="节点名称" required><n-input v-model:value="nodeCreateForm.properties.name" placeholder="输入节点名称" /></n-form-item>
          <n-form-item label="描述"><n-input v-model:value="nodeCreateForm.properties.description" type="textarea" placeholder="可选描述" :autosize="{ minRows: 3, maxRows: 6 }" /></n-form-item>
        </n-form>
        <template #action><n-space><n-button @click="showNodeCreateModal = false">取消</n-button><n-button type="primary" @click="submitNodeCreate">创建</n-button></n-space></template>
      </n-modal>

      <n-modal v-model:show="showEdgeCreateModal" preset="dialog" title="创建关系" style="width:600px">
        <n-form :model="edgeCreateForm" label-placement="left" label-width="100px">
          <n-form-item label="源节点" required><n-select v-model:value="edgeCreateForm.source" :options="availableNodes" filterable placeholder="选择源节点" /></n-form-item>
          <n-form-item label="目标节点" required><n-select v-model:value="edgeCreateForm.target" :options="availableNodes" filterable placeholder="选择目标节点" /></n-form-item>
          <n-form-item label="关系类型" required><n-input v-model:value="edgeCreateForm.type" placeholder="如：RELATES_TO" /></n-form-item>
          <n-form-item label="描述"><n-input v-model:value="edgeCreateForm.properties.description" type="textarea" placeholder="可选" :autosize="{ minRows: 2, maxRows: 4 }" /></n-form-item>
        </n-form>
        <template #action><n-space><n-button @click="showEdgeCreateModal = false">取消</n-button><n-button type="primary" @click="submitEdgeCreate">创建</n-button></n-space></template>
      </n-modal>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useMessage, useDialog } from 'naive-ui'
import {
  RefreshOutline, AddOutline, RemoveOutline,
  ExpandOutline, ContractOutline, DownloadOutline, CubeOutline,
  GitNetworkOutline, InformationCircleOutline, CreateOutline,
  TrashOutline, LinkOutline, SearchOutline
} from '@vicons/ionicons5'
import cytoscape from 'cytoscape'
import type { Core, ElementDefinition } from 'cytoscape'
import dagre from 'cytoscape-dagre'
import { getGraphData, getDocumentGraph, listDocuments, createNode, updateNode, deleteNode, createEdge, deleteEdge } from '@/api/services'

cytoscape.use(dagre)

const { t } = useI18n()
const message = useMessage()
const dialog = useDialog()
const route = useRoute()
const router = useRouter()

const nodeLimit = ref(100)
const documentDepth = ref(2)
const currentDocumentId = ref<string | null>(null)
const documentOptions = ref<Array<{ label: string; value: string }>>([])
const loading = ref(false)
const graphContainer = ref<HTMLElement | null>(null)
const graphData = ref<{ nodes: ElementDefinition[]; edges: ElementDefinition[] } | null>(null)
const layoutType = ref('dagre')
const searchQuery = ref('')
const searchResults = ref<Array<{ id: string; label: string; type: string }>>([])
const selectedNode = ref<{ id: string; label: string; properties: Record<string, any> } | null>(null)
const showNodeDetail = ref(false)
const showNodeEditModal = ref(false)
const showNodeCreateModal = ref(false)
const showEdgeCreateModal = ref(false)
const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })
const contextMenuType = ref<'node' | 'edge' | 'canvas'>('canvas')
const contextMenuTarget = ref<any>(null)
let cy: Core | null = null

// Legend
const legendItems = [
  { label: '概念 (Concept)', color: '#3b82f6' },
  { label: '文档 (Document)', color: '#1e293b' },
  { label: '实体 (Entity)', color: '#f59e0b' },
  { label: '文本块 (Chunk)', color: '#8b5cf6' },
  { label: '其他 (Other)', color: '#10b981' }
]

// Forms
const nodeEditForm = ref({ id: '', labels: [] as string[], properties: {} as Record<string, any> })
const nodeCreateForm = ref({ labels: ['Concept'], properties: { name: '' } as Record<string, any> })
const edgeCreateForm = ref({ source: '', target: '', type: 'RELATES_TO', properties: {} as Record<string, any> })

const layoutOptions = [
  { label: '层级布局', value: 'dagre' },
  { label: '圆形布局', value: 'circle' },
  { label: '网格布局', value: 'grid' },
  { label: '同心圆', value: 'concentric' },
  { label: '力导向', value: 'cose' }
]

// Search
const handleSearch = (query: string) => {
  if (!query.trim() || !graphData.value) {
    searchResults.value = []
    return
  }
  const q = query.toLowerCase()
  searchResults.value = graphData.value.nodes
    .filter((n: any) => String(n.data.label || '').toLowerCase().includes(q))
    .slice(0, 8)
    .map((n: any) => ({ id: n.data.id, label: n.data.label, type: n.data.type || 'Unknown' }))
}

const focusNode = (nodeId: string) => {
  if (!cy) return
  const node = cy.getElementById(nodeId)
  if (node.length > 0) {
    cy.animate({ center: { eles: node }, zoom: 2, duration: 500 })
    node.animate({
      style: { 'border-width': 6, 'border-color': '#6366f1' },
      duration: 300
    })
    setTimeout(() => { node.animate({ style: { 'border-width': 3, 'border-color': '#fff' }, duration: 300 }) }, 1500)
  }
  searchResults.value = []
  searchQuery.value = ''
}

// Load data
const loadDocuments = async () => {
  try {
    const result = await listDocuments(0, 100)
    const docs = result?.documents || []
    documentOptions.value = docs.map((doc: any) => ({ label: `${doc.filename} (${doc.id})`, value: doc.id }))
  } catch { /* silent */ }
}

const handleDocumentChange = async (value: string | null) => {
  currentDocumentId.value = value
  await router.replace({ path: '/graph', query: value ? { doc_id: value } : {} })
  await loadGraph()
}

const loadGraph = async () => {
  loading.value = true
  try {
    const routeDocId = (route.query.doc_id as string) || null
    currentDocumentId.value = currentDocumentId.value || routeDocId
    const docId = currentDocumentId.value

    const result = docId
      ? await getDocumentGraph(docId, documentDepth.value)
      : await getGraphData(nodeLimit.value)

    if (!result) { message.warning('无图谱数据'); return }

    let nodes: ElementDefinition[] = []
    let edges: ElementDefinition[] = []

    if (result.nodes && result.edges) {
      nodes = result.nodes.map((node: any) => ({
        data: {
          id: node.id,
          label: node.label || node.properties?.name || node.properties?.filename || node.id,
          type: node.type || (node.labels && node.labels[0]) || 'Unknown',
          degree: node.degree || 0,
          ...node.properties
        },
        classes: node.labels ? node.labels.join(' ') : (node.type || 'Unknown')
      }))

      edges = result.edges.map((edge: any) => ({
        data: {
          id: edge.id || `${edge.source}-${edge.target}-${edge.type}`,
          source: edge.source,
          target: edge.target,
          label: edge.label || edge.type,
          type: edge.type,
          ...edge.properties
        }
      }))
    }

    graphData.value = { nodes, edges }

    if (nodes.length === 0) { message.warning('图谱中未找到节点'); return }

    await nextTick()
    renderGraph()
    message.success(`已加载 ${nodes.length} 个节点和 ${edges.length} 个关系`)
  } catch (error: any) {
    message.error('加载失败')
    console.error('Failed to load graph:', error)
  } finally { loading.value = false }
}

const renderGraph = () => {
  if (!graphContainer.value || !graphData.value) return
  if (cy) cy.destroy()

  const nodeStyles = {
    selector: 'node',
    style: {
      'background-color': '#10b981',
      'label': 'data(label)',
      'width': 'mapData(degree, 0, 50, 28, 60)',
      'height': 'mapData(degree, 0, 50, 28, 60)',
      'text-valign': 'bottom',
      'text-halign': 'center',
      'text-margin-y': '6px',
      'font-size': 11,
      'font-weight': 600,
      'font-family': 'Inter, Noto Serif SC, sans-serif',
      'color': '#334155',
      'text-background-color': '#ffffff',
      'text-background-opacity': 0.85,
      'text-background-padding': '3px',
      'text-background-shape': 'roundrectangle',
      'border-width': 3,
      'border-color': '#ffffff',
      'transition-property': 'background-color, border-color, width, height',
      'transition-duration': '0.2s'
    } as any
  }

  cy = cytoscape({
    container: graphContainer.value,
    elements: [...graphData.value.nodes, ...graphData.value.edges],
    style: [
      nodeStyles,
      { selector: 'node.Concept', style: { 'background-color': '#3b82f6' } },
      { selector: 'node.Document', style: { 'background-color': '#1e293b', 'shape': 'rectangle' } },
      { selector: 'node.Entity', style: { 'background-color': '#f59e0b' } },
      { selector: 'node.Chunk', style: { 'background-color': '#8b5cf6', 'shape': 'diamond' } },
      { selector: 'node:selected', style: { 'border-width': 5, 'border-color': '#6366f1', 'shadow-color': '#6366f1', 'shadow-blur': 12, 'shadow-opacity': 0.5 } },
      { selector: 'node.highlighted', style: { 'border-width': 4, 'border-color': '#6366f1', 'shadow-color': '#6366f1', 'shadow-blur': 16, 'shadow-opacity': 0.6 } },
      { selector: 'node.dimmed', style: { 'opacity': 0.2, 'background-color': '#cbd5e1' } },
      {
        selector: 'edge',
        style: {
          'width': 2, 'line-color': '#cbd5e1', 'target-arrow-color': '#cbd5e1',
          'target-arrow-shape': 'triangle', 'curve-style': 'bezier',
          'label': 'data(label)', 'font-size': 9,
          'text-background-color': '#fff', 'text-background-opacity': 0.85,
          'text-background-padding': '2px',
          'transition-property': 'line-color, width',
          'transition-duration': '0.2s'
        } as any
      },
      { selector: 'edge:selected', style: { 'width': 4, 'line-color': '#6366f1', 'target-arrow-color': '#6366f1' } },
      { selector: 'edge.highlighted', style: { 'width': 3, 'line-color': '#6366f1', 'target-arrow-color': '#6366f1' } },
      { selector: 'edge.dimmed', style: { 'opacity': 0.08 } }
    ],
    layout: {
      name: layoutType.value,
      rankDir: 'TB',
      spacingFactor: 1.6,
      animate: true,
      animationDuration: 600,
      animationEasing: 'ease-out'
    } as any
  })

  // Node click
  cy.on('tap', 'node', (evt: any) => {
    const node = evt.target
    selectedNode.value = { id: node.id(), label: node.data('label'), properties: node.data() }
    showNodeDetail.value = true

    // Highlight connected
    const connected = node.connectedEdges().connectedNodes().add(node)
    cy!.elements().addClass('dimmed')
    connected.removeClass('dimmed').addClass('highlighted')
    node.connectedEdges().removeClass('dimmed').addClass('highlighted')
  })

  // Click background to reset
  cy.on('tap', (evt: any) => {
    if (evt.target === cy) {
      cy!.elements().removeClass('dimmed').removeClass('highlighted')
    }
  })

  // Node hover
  cy.on('mouseover', 'node', (evt: any) => {
    document.body.style.cursor = 'pointer'
    evt.target.animate({ style: { 'border-color': '#6366f1', 'border-width': 4 }, duration: 150 })
  })
  cy.on('mouseout', 'node', (evt: any) => {
    document.body.style.cursor = 'default'
    if (!evt.target.selected()) {
      evt.target.animate({ style: { 'border-color': '#ffffff', 'border-width': 3 }, duration: 150 })
    }
  })

  // Edge hover
  cy.on('mouseover', 'edge', (evt: any) => {
    evt.target.animate({ style: { 'width': 4, 'line-color': '#6366f1' }, duration: 150 })
  })
  cy.on('mouseout', 'edge', (evt: any) => {
    if (!evt.target.selected()) {
      evt.target.animate({ style: { 'width': 2, 'line-color': '#cbd5e1' }, duration: 150 })
    }
  })

  // Context menu
  cy.on('cxttap', 'node', (evt: any) => {
    evt.preventDefault()
    const node = evt.target
    contextMenuType.value = 'node'
    contextMenuTarget.value = { id: node.id(), labels: node.classes().split(' '), properties: node.data() }
    contextMenuPosition.value = { x: evt.renderedPosition.x, y: evt.renderedPosition.y }
    contextMenuVisible.value = true
  })

  cy.on('cxttap', 'edge', (evt: any) => {
    evt.preventDefault()
    const edge = evt.target
    contextMenuType.value = 'edge'
    contextMenuTarget.value = { id: edge.id(), source: edge.data('source'), target: edge.data('target'), type: edge.data('label'), properties: edge.data() }
    contextMenuPosition.value = { x: evt.renderedPosition.x, y: evt.renderedPosition.y }
    contextMenuVisible.value = true
  })

  cy.on('cxttap', (evt: any) => {
    if (evt.target === cy) {
      evt.preventDefault()
      contextMenuType.value = 'canvas'
      contextMenuTarget.value = null
      contextMenuPosition.value = { x: evt.renderedPosition.x, y: evt.renderedPosition.y }
      contextMenuVisible.value = true
    }
  })

  cy.on('tap', () => { contextMenuVisible.value = false })
}

// Controls
const zoomIn = () => { if (cy) cy.animate({ zoom: (cy.zoom() * 1.3), duration: 300 }) }
const zoomOut = () => { if (cy) cy.animate({ zoom: (cy.zoom() * 0.7), duration: 300 }) }
const fitView = () => { if (cy) cy.animate({ fit: { eles: cy.elements(), padding: 50 }, duration: 500 }) }
const resetView = () => { if (cy) { cy.zoom(1); cy.center() } }

const handleLayoutChange = () => {
  if (cy && graphData.value) {
    cy.layout({ name: layoutType.value, animate: true, animationDuration: 600, spacingFactor: 1.6 } as any).run()
  }
}

const exportGraph = () => {
  if (!cy) return
  const png = cy.png({ full: true, scale: 3, bg: '#ffffff' })
  const link = document.createElement('a')
  link.download = `graphforge-graph-${Date.now()}.png`
  link.href = png
  link.click()
  message.success('图谱已导出为 PNG')
}

const resetDocumentFilter = async () => {
  currentDocumentId.value = null
  await router.replace({ path: '/graph' })
  await loadGraph()
}

// CRUD handlers (same logic as original)
const handleEditNode = () => {
  if (!contextMenuTarget.value) return
  const t = contextMenuTarget.value
  nodeEditForm.value = { id: t.id, labels: t.labels || [], properties: { ...t.properties } }
  showNodeEditModal.value = true
  contextMenuVisible.value = false
}

const handleCreateNode = () => {
  nodeCreateForm.value = { labels: ['Concept'], properties: { name: '' } }
  showNodeCreateModal.value = true
  contextMenuVisible.value = false
}

const handleDeleteNode = () => {
  if (!contextMenuTarget.value) return
  dialog.warning({
    title: '确认删除',
    content: `确定删除 "${contextMenuTarget.value.properties?.name || contextMenuTarget.value.id}"？`,
    positiveText: '删除',
    onPositiveClick: async () => {
      try { await deleteNode(contextMenuTarget.value.id, true); message.success('已删除'); await loadGraph() }
      catch (e: any) { message.error('删除失败: ' + (e.response?.data?.detail || e.message)) }
    }
  })
  contextMenuVisible.value = false
}

const submitNodeEdit = async () => {
  try {
    await updateNode(nodeEditForm.value.id, {
      labels: nodeEditForm.value.labels.length > 0 ? nodeEditForm.value.labels : undefined,
      properties: nodeEditForm.value.properties
    })
    message.success('已更新')
    showNodeEditModal.value = false
    await loadGraph()
  } catch (e: any) { message.error('更新失败: ' + (e.response?.data?.detail || e.message)) }
}

const submitNodeCreate = async () => {
  try {
    if (!nodeCreateForm.value.properties.name) { message.error('请输入节点名称'); return }
    await createNode({ labels: nodeCreateForm.value.labels, properties: nodeCreateForm.value.properties })
    message.success('已创建')
    showNodeCreateModal.value = false
    await loadGraph()
  } catch (e: any) { message.error('创建失败: ' + (e.response?.data?.detail || e.message)) }
}

const handleCreateEdge = () => {
  if (contextMenuType.value === 'node' && contextMenuTarget.value) {
    edgeCreateForm.value.source = contextMenuTarget.value.id
    edgeCreateForm.value.target = ''
  } else { edgeCreateForm.value.source = ''; edgeCreateForm.value.target = '' }
  edgeCreateForm.value.type = 'RELATES_TO'
  edgeCreateForm.value.properties = {}
  showEdgeCreateModal.value = true
  contextMenuVisible.value = false
}

const handleDeleteEdge = () => {
  if (!contextMenuTarget.value) return
  const et = contextMenuTarget.value
  dialog.warning({
    title: '确认删除',
    content: `确定删除 "${et.source}" → "${et.target}" (${et.type})？`,
    positiveText: '删除',
    onPositiveClick: async () => {
      try { await deleteEdge(et.source, et.target, et.type); message.success('已删除'); await loadGraph() }
      catch (e: any) { message.error('删除失败: ' + (e.response?.data?.detail || e.message)) }
    }
  })
  contextMenuVisible.value = false
}

const submitEdgeCreate = async () => {
  try {
    if (!edgeCreateForm.value.source || !edgeCreateForm.value.target) { message.error('请选择源和目标节点'); return }
    if (!edgeCreateForm.value.type) { message.error('请输入关系类型'); return }
    await createEdge({ source: edgeCreateForm.value.source, target: edgeCreateForm.value.target, type: edgeCreateForm.value.type, properties: edgeCreateForm.value.properties })
    message.success('已创建')
    showEdgeCreateModal.value = false
    await loadGraph()
  } catch (e: any) { message.error('创建失败: ' + (e.response?.data?.detail || e.message)) }
}

const availableNodes = computed(() => {
  if (!graphData.value) return []
  return graphData.value.nodes.map((n: any) => ({ label: n.data.label || n.data.id, value: n.data.id }))
})

const chunkCount = computed(() => {
  if (!graphData.value) return 0
  return graphData.value.nodes.filter((n: any) => {
    const t = ((n.data.type || '') + (n.classes || '')).toLowerCase()
    return t.includes('chunk')
  }).length
})

watch(() => route.query.doc_id, () => loadGraph())

onMounted(() => { loadDocuments(); loadGraph() })
onUnmounted(() => { if (cy) cy.destroy() })
</script>

<style lang="scss" scoped>
.graph-page {
  padding: 24px 36px;
  min-height: calc(100vh - 64px);
  position: relative;

  .page-bg {
    position: fixed; inset: 0;
    background:
      radial-gradient(ellipse at 20% 20%, rgba(16, 185, 129, 0.05) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 80%, rgba(52, 211, 153, 0.05) 0%, transparent 50%);
    pointer-events: none; z-index: 0;
  }

  > * { position: relative; z-index: 1; }
}

.graph-header {
  margin-bottom: 24px;
  padding: 24px 32px;

  .graph-title { font-size: 32px; font-weight: 800; margin: 0 0 6px; letter-spacing: -0.5px; }
  .graph-subtitle { font-size: 14px; color: var(--color-text-muted); margin: 0; font-weight: 500; }
}

.graph-card {
  :deep(.n-card__content) { padding: 24px; }
}

// Control Panel
.control-panel {
  padding: 18px 22px;
  background: linear-gradient(135deg, rgba(240, 253, 244, 0.5), rgba(255, 255, 255, 0.5));
  backdrop-filter: blur(10px);
  border-radius: var(--radius-xl);
  margin-bottom: 20px;
  border: 1px solid rgba(16, 185, 129, 0.12);
  box-shadow: var(--shadow-sm), inset 0 1px 0 rgba(255, 255, 255, 0.8);

  .control-item {
    display: flex; align-items: center; gap: 8px;
  }

  :deep(.n-button) { border-radius: var(--radius-md); font-weight: 600; }
  :deep(.n-button--primary-type) { box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25); }
}

// Stats Bar
.stats-bar {
  display: flex; gap: 16px; padding: 16px;
  background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(248,250,252,0.9));
  border-radius: var(--radius-xl);
  margin-bottom: 20px;
  border: 1px solid rgba(226, 232, 240, 0.6);
  box-shadow: var(--shadow-sm), inset 0 1px 0 rgba(255,255,255,0.8);

  .stat-item {
    display: flex; align-items: center; gap: 12px;
    padding: 12px 20px; border-radius: var(--radius-lg); flex: 1;
    transition: all var(--transition-base);
    box-shadow: var(--shadow-sm);
    background: white;

    &:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }

    &.stat-blue .n-icon { color: #3b82f6; }
    &.stat-green .n-icon { color: #10b981; }
    &.stat-yellow .n-icon { color: #f59e0b; }
    &.stat-purple .n-icon { color: #8b5cf6; }

    .stat-label { font-size: 13px; color: var(--color-text-secondary); font-weight: 600; }
    .stat-value {
      font-size: 22px; font-weight: 800; color: var(--color-text);
      letter-spacing: -0.3px;
      &.name { font-size: 16px; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    }
  }
}

// Graph Wrapper
.graph-wrapper {
  position: relative; height: 680px;
  border-radius: var(--radius-xl); overflow: hidden;
  background: linear-gradient(135deg, #f8fafc, #f1f5f9, #e2e8f0);
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: inset 0 2px 8px rgba(0,0,0,0.03), var(--shadow-md);
}

.graph-container {
  width: 100%; height: 100%;
  background: #ffffff;
  position: relative;

  &::before {
    content: ''; position: absolute; inset: 0;
    background:
      radial-gradient(circle at 20% 30%, rgba(99,102,241,0.02) 0%, transparent 50%),
      radial-gradient(circle at 80% 70%, rgba(16,185,129,0.02) 0%, transparent 50%);
    pointer-events: none;
  }
}

// Search results
.search-results {
  position: absolute; top: 12px; left: 12px;
  background: var(--glass-card); border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg); z-index: 20;
  max-height: 280px; overflow-y: auto; min-width: 220px;
  padding: 6px;

  .search-result-item {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 12px; border-radius: var(--radius-sm);
    cursor: pointer; font-size: 13px; font-weight: 500;
    color: var(--color-text); transition: all var(--transition-fast);

    &:hover { background: var(--color-primary-subtle); }
  }
}

// Legend
.graph-legend {
  position: absolute; bottom: 16px; left: 16px;
  background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(248,250,252,0.98));
  backdrop-filter: blur(20px); padding: 16px 20px;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg), inset 0 1px 0 rgba(255,255,255,0.8);
  border: 1px solid rgba(255,255,255,0.6);
  z-index: 10;

  .legend-title { font-weight: 700; font-size: 13px; color: var(--color-text); margin-bottom: 10px; }
  .legend-item {
    display: flex; align-items: center; gap: 10px;
    font-size: 12px; color: var(--color-text-secondary);
    font-weight: 500; padding: 4px; border-radius: var(--radius-sm);
    transition: all var(--transition-fast);

    &:hover { background: rgba(0,0,0,0.02); }
    .legend-color {
      width: 18px; height: 18px; border-radius: 50%;
      border: 2px solid #fff;
      box-shadow: 0 2px 6px rgba(0,0,0,0.12);
      transition: transform var(--transition-fast);
    }
    &:hover .legend-color { transform: scale(1.15); }
  }
}

// Loading
.loading-overlay {
  position: absolute; inset: 0;
  background: rgba(255,255,255,0.95);
  backdrop-filter: blur(12px);
  display: flex; align-items: center; justify-content: center;
  z-index: 100; border-radius: var(--radius-xl);

  .loading-text { margin-top: 16px; font-size: 16px; color: var(--color-text-secondary); font-weight: 600; }
}

.empty-state {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%); z-index: 10;
}

// Drawer
.node-detail {
  :deep(.n-descriptions-table-wrapper) { border-radius: var(--radius-lg); overflow: hidden; }
}

// Context Menu
.context-menu {
  position: fixed;
  background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(248,250,252,0.98));
  backdrop-filter: blur(20px);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl), inset 0 1px 0 rgba(255,255,255,0.8);
  border: 1px solid rgba(255,255,255,0.6);
  padding: 6px; z-index: 1000; min-width: 160px;

  .context-menu-item {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 12px; border-radius: var(--radius-sm);
    cursor: pointer; font-size: 13px; font-weight: 500;
    color: var(--color-text); transition: all var(--transition-fast);

    &:hover { background: rgba(16, 185, 129, 0.08); color: #10b981; .n-icon { color: #10b981; } }
    &.danger:hover { background: rgba(239, 68, 68, 0.08); color: #ef4444; .n-icon { color: #ef4444; } }
  }
}

// Modal
:deep(.n-modal) {
  .n-dialog { border-radius: var(--radius-2xl); overflow: hidden; }
  .n-dialog__title { font-size: 20px; font-weight: 700; }
}

// Button group
:deep(.n-button-group) {
  border-radius: var(--radius-md); overflow: hidden;
  box-shadow: var(--shadow-sm);
  .n-button { border-radius: 0; }
}

// Animations
.fade-enter-active { transition: opacity 0.3s ease; }
.fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
