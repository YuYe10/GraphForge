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
/**
 * Graph.vue - 图谱可视化视图 / Graph Visualization View
 *
 * 【功能 / Functionality】
 * 1. Cytoscape.js 知识图谱渲染 / Cytoscape.js knowledge graph rendering
 * 2. 节点/关系 CRUD 操作 / Node & edge CRUD operations
 * 3. 右键上下文菜单 / Right-click context menu
 * 4. 节点搜索定位 / Node search and focus
 * 5. 多布局切换（层级/圆形/网格/同心圆/力导向）
 *    / Multiple layout switching (dagre/circle/grid/concentric/cose)
 * 6. 文档筛选与深度控制 / Document filtering with depth control
 * 7. 缩放/平移/视图重置 / Zoom, pan, and view reset
 * 8. PNG 导出 / PNG export
 *
 * 【角色 / Role】
 * 核心交互式知识图谱可视化页面，提供图形化的节点-关系探索和编辑能力。
 * Core interactive knowledge graph page with graphical node-relationship
 * exploration and editing capabilities.
 */

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

// 注册 dagre 层级布局插件 / Register dagre hierarchical layout plugin
cytoscape.use(dagre)

const { t } = useI18n()
const message = useMessage()
const dialog = useDialog()
const route = useRoute()
const router = useRouter()

// ===========================================================================
// 响应式状态 / Reactive State
// ===========================================================================

// -- 图谱数据与 Cytoscape 实例 / Graph data & Cytoscape instance --------------

/** Cytoscape 核心实例引用（非响应式，由 renderGraph 创建和管理） */
let cy: Core | null = null

/** DOM 容器引用，用于挂载 Cytoscape / DOM container ref for mounting Cytoscape */
const graphContainer = ref<HTMLElement | null>(null)

/** 图谱原始数据（节点和边列表） / Raw graph data (nodes & edges arrays) */
const graphData = ref<{ nodes: ElementDefinition[]; edges: ElementDefinition[] } | null>(null)

/** 数据加载中状态 / Data loading state */
const loading = ref(false)

// -- 控制参数 / Control parameters -------------------------------------------

/** 最大节点加载数 / Maximum node count to load */
const nodeLimit = ref(100)

/** 文档筛选深度（仅筛选模式可用） / Document filter depth (filter mode only) */
const documentDepth = ref(2)

/** 当前筛选的文档 ID / Currently filtered document ID */
const currentDocumentId = ref<string | null>(null)

/** 文档选项列表（用于筛选下拉框） / Document option list for filter select */
const documentOptions = ref<Array<{ label: string; value: string }>>([])

/** 当前布局类型 / Current layout type */
const layoutType = ref('dagre')

/** 可用布局选项 / Available layout options */
const layoutOptions = [
  { label: '层级布局', value: 'dagre' },
  { label: '圆形布局', value: 'circle' },
  { label: '网格布局', value: 'grid' },
  { label: '同心圆', value: 'concentric' },
  { label: '力导向', value: 'cose' }
]

// -- 搜索 / Search -----------------------------------------------------------

/** 搜索关键词 / Search query text */
const searchQuery = ref('')

/** 搜索结果列表 / Search result items (id, label, type) */
const searchResults = ref<Array<{ id: string; label: string; type: string }>>([])

// -- 选中状态 / Selection state -----------------------------------------------

/** 当前选中的节点详情 / Currently selected node details */
const selectedNode = ref<{ id: string; label: string; properties: Record<string, any> } | null>(null)

/** 控制节点详情抽屉的显示 / Controls node detail drawer visibility */
const showNodeDetail = ref(false)

// -- 上下文菜单 / Context menu ------------------------------------------------

/** 上下文菜单是否可见 / Whether context menu is visible */
const contextMenuVisible = ref(false)

/** 上下文菜单位置（像素坐标） / Context menu position (pixel coords) */
const contextMenuPosition = ref({ x: 0, y: 0 })

/** 上下文菜单触发的元素类型 / Target element type for context menu */
const contextMenuType = ref<'node' | 'edge' | 'canvas'>('canvas')

/** 上下文菜单的目标对象引用 / Reference to the target element */
const contextMenuTarget = ref<any>(null)

// -- CRUD 表单 / CRUD form state ---------------------------------------------

/** 编辑节点弹窗可见 / Node edit modal visibility */
const showNodeEditModal = ref(false)

/** 创建节点弹窗可见 / Node create modal visibility */
const showNodeCreateModal = ref(false)

/** 创建关系弹窗可见 / Edge create modal visibility */
const showEdgeCreateModal = ref(false)

/** 节点编辑表单数据 / Node edit form model */
const nodeEditForm = ref({ id: '', labels: [] as string[], properties: {} as Record<string, any> })

/** 节点创建表单数据 / Node create form model */
const nodeCreateForm = ref({ labels: ['Concept'], properties: { name: '' } as Record<string, any> })

/** 关系创建表单数据 / Edge create form model */
const edgeCreateForm = ref({ source: '', target: '', type: 'RELATES_TO', properties: {} as Record<string, any> })

// ===========================================================================
// 图例配置 / Legend Configuration
// ===========================================================================

/**
 * 节点类型图例 / Node type legend
 * 定义了不同节点类型对应的颜色和显示标签，与 Cytoscape stylesheet 保持一致。
 * Defines colors and labels for each node type, matching the Cytoscape stylesheet.
 */
const legendItems = [
  { label: '概念 (Concept)', color: '#3b82f6' },
  { label: '文档 (Document)', color: '#1e293b' },
  { label: '实体 (Entity)', color: '#f59e0b' },
  { label: '文本块 (Chunk)', color: '#8b5cf6' },
  { label: '其他 (Other)', color: '#10b981' }
]

// ===========================================================================
// 计算属性 / Computed Properties
// ===========================================================================

/**
 * 可用节点列表（用于创建关系时的选择器）
 * Available node list for edge creation selectors.
 * 从 graphData.nodes 映射为 {label, value} 格式。
 * Mapped from graphData.nodes into {label, value} format.
 */
const availableNodes = computed(() => {
  if (!graphData.value) return []
  return graphData.value.nodes.map((n: any) => ({ label: n.data.label || n.data.id, value: n.data.id }))
})

/**
 * 文档筛选模式下 Chunk 类型节点计数
 * Chunk-type node count when a document filter is active.
 * 同时检查 data.type 和 classes 字段以兼容不同后端数据格式。
 * Checks both data.type and classes fields for backend format compatibility.
 */
const chunkCount = computed(() => {
  if (!graphData.value) return 0
  return graphData.value.nodes.filter((n: any) => {
    const t = ((n.data.type || '') + (n.classes || '')).toLowerCase()
    return t.includes('chunk')
  }).length
})

// ===========================================================================
// 搜索功能 / Search Functionality
// ===========================================================================

/**
 * 处理搜索输入 / Handle search query input
 *
 * 在当前图谱数据中按节点标签模糊搜索，最多返回 8 条结果。
 * Performs fuzzy search on node labels within the current graph data,
 * returning at most 8 results.
 *
 * @param query - 搜索关键词 / Search query string
 */
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

/**
 * 聚焦到指定节点 / Focus camera on a specific node
 *
 * 1. 使用 cy.animate() 平滑平移/缩放到目标节点
 * 2. 临时高亮节点边框（1.5s 后恢复）
 * 3. 清空搜索结果和搜索框
 *
 * @param nodeId - 目标节点 ID / Target node ID
 */
const focusNode = (nodeId: string) => {
  if (!cy) return
  const node = cy.getElementById(nodeId)
  if (node.length > 0) {
    // 将视口居中于该节点并放大到 2x / Center viewport on node and zoom to 2x
    cy.animate({ center: { eles: node }, zoom: 2, duration: 500 })
    // 临时高亮边框 / Temporary border highlight
    node.animate({
      style: { 'border-width': 6, 'border-color': '#6366f1' },
      duration: 300
    })
    // 1.5 秒后恢复默认样式 / Restore default style after 1.5s
    setTimeout(() => { node.animate({ style: { 'border-width': 3, 'border-color': '#fff' }, duration: 300 }) }, 1500)
  }
  // 清空搜索状态 / Clear search state
  searchResults.value = []
  searchQuery.value = ''
}

// ===========================================================================
// 数据加载 / Data Loading
// ===========================================================================

/**
 * 加载文档列表（用于筛选下拉框）
 * Load document list for the filter dropdown.
 * 组件挂载时自动调用，静默失败（catch 为空）。
 * Auto-invoked on mount; failures are silent.
 */
const loadDocuments = async () => {
  try {
    const result = await listDocuments(0, 100)
    const docs = result?.documents || []
    documentOptions.value = docs.map((doc: any) => ({ label: `${doc.filename} (${doc.id})`, value: doc.id }))
  } catch { /* silent */ }
}

/**
 * 处理文档筛选变更 / Handle document filter change
 *
 * 更新 URL query 参数并重新加载图谱。
 * Updates URL query parameter and reloads the graph.
 *
 * @param value - 选中的文档 ID 或 null / Selected document ID or null
 */
const handleDocumentChange = async (value: string | null) => {
  currentDocumentId.value = value
  await router.replace({ path: '/graph', query: value ? { doc_id: value } : {} })
  await loadGraph()
}

/**
 * 加载图谱数据 / Load graph data from API
 *
 * 根据文档筛选状态决定调用哪个 API：
 * - 有文档筛选 → getDocumentGraph(docId, depth) 获取子图
 * - 无文档筛选 → getGraphData(limit) 获取全图
 *
 * 对后端返回的节点和边数据进行标准化转换，适配 Cytoscape 的 ElementDefinition 格式。
 * Standardizes backend node/edge data into Cytoscape's ElementDefinition format.
 */
const loadGraph = async () => {
  loading.value = true
  try {
    // 优先使用 URL 中的 doc_id 参数 / Prefer doc_id from URL query
    const routeDocId = (route.query.doc_id as string) || null
    currentDocumentId.value = currentDocumentId.value || routeDocId
    const docId = currentDocumentId.value

    // 根据是否筛选文档选择 API / Choose API based on document filter
    const result = docId
      ? await getDocumentGraph(docId, documentDepth.value)
      : await getGraphData(nodeLimit.value)

    if (!result) { message.warning('无图谱数据'); return }

    let nodes: ElementDefinition[] = []
    let edges: ElementDefinition[] = []

    if (result.nodes && result.edges) {
      // 节点数据转换：映射 id/label/type/degree + 原生属性 + classes
      // Node data transformation: map id/label/type/degree + raw properties + classes
      nodes = result.nodes.map((node: any) => ({
        data: {
          id: node.id,
          label: node.label || node.properties?.name || node.properties?.filename || node.id,
          type: node.type || (node.labels && node.labels[0]) || 'Unknown',
          degree: node.degree || 0,
          ...node.properties
        },
        // classes 用于 Cytoscape 的选择器样式匹配（如 node.Concept）
        // classes used for Cytoscape selector-based styling (e.g. node.Concept)
        classes: node.labels ? node.labels.join(' ') : (node.type || 'Unknown')
      }))

      // 边数据转换：生成唯一 ID，映射 source/target/label/type + 原生属性
      // Edge data transformation: generate unique ID, map source/target/label/type + properties
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

    // 等待 DOM 更新后再渲染 Cytoscape / Wait for DOM update before rendering
    await nextTick()
    renderGraph()
    message.success(`已加载 ${nodes.length} 个节点和 ${edges.length} 个关系`)
  } catch (error: any) {
    message.error('加载失败')
    console.error('Failed to load graph:', error)
  } finally { loading.value = false }
}

// ===========================================================================
// Cytoscape 渲染 / Cytoscape Rendering
// ===========================================================================

/**
 * 渲染图谱 / Render the graph using Cytoscape.js
 *
 * 核心渲染函数，执行以下操作：
 * 1. 销毁旧的 Cytoscape 实例 / Destroy old Cytoscape instance
 * 2. 定义样式表（节点按类型着色、尺寸按度映射、边箭头和标签样式）
 *    / Define stylesheet (node color by type, size by degree, edge arrows & labels)
 * 3. 初始化 Cytoscape 实例 / Initialize Cytoscape instance
 * 4. 绑定交互事件（点击、悬停、右键菜单） / Bind interaction events (tap, hover, context menu)
 */
const renderGraph = () => {
  if (!graphContainer.value || !graphData.value) return
  // 销毁旧实例，防止多次创建导致的内存泄漏和事件重复绑定
  // Destroy old instance to prevent memory leaks and duplicate event bindings
  if (cy) cy.destroy()

  // 默认节点样式 / Default node style
  const nodeStyles = {
    selector: 'node',
    style: {
      'background-color': '#10b981',
      'label': 'data(label)',
      // 节点尺寸根据 degree（连接数）动态映射：degree 0→28px, 50→60px
      // Node size mapped from degree: degree 0→28px, degree 50→60px
      'width': 'mapData(degree, 0, 50, 28, 60)',
      'height': 'mapData(degree, 0, 50, 28, 60)',
      'text-valign': 'bottom',
      'text-halign': 'center',
      'text-margin-y': '6px',
      'font-size': 11,
      'font-weight': 600,
      'font-family': 'Inter, Noto Serif SC, sans-serif',
      'color': '#334155',
      // 文字背景（圆角矩形标签底） / Text background (rounded rectangle label bg)
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
      // 按节点类型着色 / Per-type node coloring
      { selector: 'node.Concept', style: { 'background-color': '#3b82f6' } },
      { selector: 'node.Document', style: { 'background-color': '#1e293b', 'shape': 'rectangle' } },
      { selector: 'node.Entity', style: { 'background-color': '#f59e0b' } },
      { selector: 'node.Chunk', style: { 'background-color': '#8b5cf6', 'shape': 'diamond' } },
      // 选中 / Selected state
      { selector: 'node:selected', style: { 'border-width': 5, 'border-color': '#6366f1', 'shadow-color': '#6366f1', 'shadow-blur': 12, 'shadow-opacity': 0.5 } },
      // 高亮（点击关联元素）/ Highlighted (click-connected elements)
      { selector: 'node.highlighted', style: { 'border-width': 4, 'border-color': '#6366f1', 'shadow-color': '#6366f1', 'shadow-blur': 16, 'shadow-opacity': 0.6 } },
      // 暗淡（非关联元素）/ Dimmed (non-connected elements)
      { selector: 'node.dimmed', style: { 'opacity': 0.2, 'background-color': '#cbd5e1' } },
      // 边默认样式 / Default edge style (bezier curve with arrow)
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
      // 边选中状态 / Edge selected state
      { selector: 'edge:selected', style: { 'width': 4, 'line-color': '#6366f1', 'target-arrow-color': '#6366f1' } },
      // 边高亮 / Edge highlighted state
      { selector: 'edge.highlighted', style: { 'width': 3, 'line-color': '#6366f1', 'target-arrow-color': '#6366f1' } },
      // 边暗淡 / Edge dimmed state
      { selector: 'edge.dimmed', style: { 'opacity': 0.08 } }
    ],
    layout: {
      name: layoutType.value,
      rankDir: 'TB',                    // dagre 层级方向：上到下 / Dagre rank direction: top-to-bottom
      spacingFactor: 1.6,               // 节点间距 / Node spacing factor
      animate: true,                    // 启用布局过渡动画 / Enable layout transition animation
      animationDuration: 600,
      animationEasing: 'ease-out'
    } as any
  })

  // -----------------------------------------------------------------------
  // 事件绑定 / Event Bindings
  // -----------------------------------------------------------------------

  /** 点击节点：打开详情抽屉并高亮关联子图 */
  /** Click node: open detail drawer and highlight connected subgraph */
  cy.on('tap', 'node', (evt: any) => {
    const node = evt.target
    selectedNode.value = { id: node.id(), label: node.data('label'), properties: node.data() }
    showNodeDetail.value = true

    // 高亮关联：将全部元素设为 dimmed，再将当前节点及其连接节点和边设为 highlighted
    // Highlight connected: dim all elements, then highlight the node and its neighbors
    const connected = node.connectedEdges().connectedNodes().add(node)
    cy!.elements().addClass('dimmed')
    connected.removeClass('dimmed').addClass('highlighted')
    node.connectedEdges().removeClass('dimmed').addClass('highlighted')
  })

  /** 点击画布空白处：重置高亮 / Click canvas background: reset highlights */
  cy.on('tap', (evt: any) => {
    if (evt.target === cy) {
      cy!.elements().removeClass('dimmed').removeClass('highlighted')
    }
  })

  /** 节点悬停：变手型指针 + 边框高亮 / Node hover: pointer cursor + border highlight */
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

  /** 边悬停：加粗变色 / Edge hover: thicken and change color */
  cy.on('mouseover', 'edge', (evt: any) => {
    evt.target.animate({ style: { 'width': 4, 'line-color': '#6366f1' }, duration: 150 })
  })
  cy.on('mouseout', 'edge', (evt: any) => {
    if (!evt.target.selected()) {
      evt.target.animate({ style: { 'width': 2, 'line-color': '#cbd5e1' }, duration: 150 })
    }
  })

  /** 右键节点：显示包含编辑/删除选项的上下文菜单 */
  /** Right-click node: show context menu with edit/delete options */
  cy.on('cxttap', 'node', (evt: any) => {
    evt.preventDefault()
    const node = evt.target
    contextMenuType.value = 'node'
    contextMenuTarget.value = { id: node.id(), labels: node.classes().split(' '), properties: node.data() }
    contextMenuPosition.value = { x: evt.renderedPosition.x, y: evt.renderedPosition.y }
    contextMenuVisible.value = true
  })

  /** 右键边：显示删除选项 / Right-click edge: show delete option */
  cy.on('cxttap', 'edge', (evt: any) => {
    evt.preventDefault()
    const edge = evt.target
    contextMenuType.value = 'edge'
    contextMenuTarget.value = { id: edge.id(), source: edge.data('source'), target: edge.data('target'), type: edge.data('label'), properties: edge.data() }
    contextMenuPosition.value = { x: evt.renderedPosition.x, y: evt.renderedPosition.y }
    contextMenuVisible.value = true
  })

  /** 右键画布：显示创建选项 / Right-click canvas: show create options */
  cy.on('cxttap', (evt: any) => {
    if (evt.target === cy) {
      evt.preventDefault()
      contextMenuType.value = 'canvas'
      contextMenuTarget.value = null
      contextMenuPosition.value = { x: evt.renderedPosition.x, y: evt.renderedPosition.y }
      contextMenuVisible.value = true
    }
  })

  /** 点击任意位置关闭上下文菜单 / Click anywhere to close context menu */
  cy.on('tap', () => { contextMenuVisible.value = false })
}

// ===========================================================================
// 视图控制 / View Controls
// ===========================================================================

/** 放大 / Zoom in (130%) */
const zoomIn = () => { if (cy) cy.animate({ zoom: (cy.zoom() * 1.3), duration: 300 }) }

/** 缩小 / Zoom out (70%) */
const zoomOut = () => { if (cy) cy.animate({ zoom: (cy.zoom() * 0.7), duration: 300 }) }

/** 自适应适配所有元素 / Fit view to all elements with 50px padding */
const fitView = () => { if (cy) cy.animate({ fit: { eles: cy.elements(), padding: 50 }, duration: 500 }) }

/** 重置缩放和平移 / Reset zoom to 1x and center */
const resetView = () => { if (cy) { cy.zoom(1); cy.center() } }

// ===========================================================================
// 布局切换 / Layout Switching
// ===========================================================================

/**
 * 切换图谱布局 / Change graph layout
 * 可选的布局类型在 layoutOptions 中定义。
 * Available layout types are defined in layoutOptions.
 */
const handleLayoutChange = () => {
  if (cy && graphData.value) {
    cy.layout({ name: layoutType.value, animate: true, animationDuration: 600, spacingFactor: 1.6 } as any).run()
  }
}

// ===========================================================================
// 导出 / Export
// ===========================================================================

/**
 * 导出图谱为 PNG 图片 / Export graph as PNG image
 *
 * 使用 Cytoscape 的 png() 方法生成高分辨率（3x）PNG，
 * 然后通过动态创建的 <a> 标签触发下载。
 * Uses Cytoscape's png() method to generate a high-resolution (3x) PNG,
 * then triggers download via a dynamically created <a> element.
 */
const exportGraph = () => {
  if (!cy) return
  const png = cy.png({ full: true, scale: 3, bg: '#ffffff' })
  const link = document.createElement('a')
  link.download = `graphforge-graph-${Date.now()}.png`
  link.href = png
  link.click()
  message.success('图谱已导出为 PNG')
}

// ===========================================================================
// 文档筛选重置 / Document Filter Reset
// ===========================================================================

/**
 * 重置文档筛选 / Reset document filter to show full graph
 * 清除 currentDocumentId 和 URL query 参数，重新加载全图。
 * Clears currentDocumentId and URL query param, reloads full graph.
 */
const resetDocumentFilter = async () => {
  currentDocumentId.value = null
  await router.replace({ path: '/graph' })
  await loadGraph()
}

// ===========================================================================
// CRUD: 节点/关系操作处理器 / Node & Edge Operation Handlers
// ===========================================================================

// -- 编辑节点 / Edit node ---------------------------------------------------

/** 打开节点编辑弹窗（从上下文菜单） / Open node edit modal (from context menu) */
const handleEditNode = () => {
  if (!contextMenuTarget.value) return
  const t = contextMenuTarget.value
  nodeEditForm.value = { id: t.id, labels: t.labels || [], properties: { ...t.properties } }
  showNodeEditModal.value = true
  contextMenuVisible.value = false
}

/** 提交节点编辑 / Submit node edit changes to API */
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

// -- 创建节点 / Create node -------------------------------------------------

/** 打开创建节点弹窗 / Open node creation modal */
const handleCreateNode = () => {
  nodeCreateForm.value = { labels: ['Concept'], properties: { name: '' } }
  showNodeCreateModal.value = true
  contextMenuVisible.value = false
}

/** 提交节点创建 / Submit node creation to API */
const submitNodeCreate = async () => {
  try {
    if (!nodeCreateForm.value.properties.name) { message.error('请输入节点名称'); return }
    await createNode({ labels: nodeCreateForm.value.labels, properties: nodeCreateForm.value.properties })
    message.success('已创建')
    showNodeCreateModal.value = false
    await loadGraph()
  } catch (e: any) { message.error('创建失败: ' + (e.response?.data?.detail || e.message)) }
}

// -- 删除节点 / Delete node -------------------------------------------------

/** 删除节点（带确认对话框，从上下文菜单触发） / Delete node with confirmation dialog */
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

// -- 创建关系 / Create edge -------------------------------------------------

/** 打开创建关系弹窗（如果从节点上下文菜单触发，自动填入源节点） */
/** Open edge creation modal; auto-fill source if triggered from node context menu */
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

/** 提交关系创建 / Submit edge creation to API */
const submitEdgeCreate = async () => {
  try {
    if (!edgeCreateForm.value.source || !edgeCreateForm.value.target) { message.error('请选择源和目标节点'); return }
    if (!edgeCreateForm.value.type) { message.error('请输入关系类型'); return }
    await createEdge({
      source: edgeCreateForm.value.source,
      target: edgeCreateForm.value.target,
      type: edgeCreateForm.value.type,
      properties: edgeCreateForm.value.properties
    })
    message.success('已创建')
    showEdgeCreateModal.value = false
    await loadGraph()
  } catch (e: any) { message.error('创建失败: ' + (e.response?.data?.detail || e.message)) }
}

// -- 删除关系 / Delete edge -------------------------------------------------

/**
 * 删除关系（带确认对话框，从上下文菜单触发）
 * Delete edge with confirmation dialog (triggered from context menu)
 * 使用 source-target-type 三元组唯一标识一条关系。
 * Uses source-target-type triple as the unique edge identifier.
 */
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

// ===========================================================================
// 侦听器 / Watchers
// ===========================================================================

/**
 * 监听路由 query 中 doc_id 的变化
 * Watch for doc_id changes in route query.
 * 当用户通过外部链接或浏览器前进/后退切换文档筛选时，自动加载对应子图。
 * Auto-loads the corresponding subgraph when document filter changes via
 * external links or browser navigation.
 */
watch(() => route.query.doc_id, () => loadGraph())

// ===========================================================================
// 生命周期钩子 / Lifecycle Hooks
// ===========================================================================

/** 组件挂载时加载文档列表和图谱数据 */
onMounted(() => { loadDocuments(); loadGraph() })

/**
 * 组件卸载时销毁 Cytoscape 实例，防止内存泄漏
 * Destroy Cytoscape instance on unmount to prevent memory leaks.
 */
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
