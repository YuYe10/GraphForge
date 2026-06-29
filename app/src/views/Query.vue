<template>
  <div class="query-page">
    <div class="page-bg"></div>

    <!-- Header -->
    <div class="query-header glass-card">
      <h1 class="query-title gradient-text-blue">图谱查询</h1>
      <p class="query-subtitle">使用 Cypher 查询语言探索知识图谱 · Interactive Knowledge Query</p>
    </div>

    <n-card class="query-card glass-card" :bordered="false">
      <n-tabs v-model:value="activeTab" type="line" animated>
        <!-- Cypher Query Tab -->
        <n-tab-pane name="cypher" tab="🔍 Cypher 查询">
          <n-space vertical :size="16">
            <div class="cypher-input-wrapper">
              <div class="cypher-toolbar">
                <n-space :size="8">
                  <n-tag v-for="tpl in cypherTemplates" :key="tpl.label" size="small" :bordered="false" type="info" style="cursor:pointer" @click="cypherQuery = tpl.query">
                    {{ tpl.label }}
                  </n-tag>
                </n-space>
                <n-button text size="small" @click="clearHistory" v-if="queryHistory.length > 0">清空历史</n-button>
              </div>
              <n-input
                v-model:value="cypherQuery"
                type="textarea"
                :rows="6"
                :placeholder="'MATCH (n) RETURN n LIMIT 25'"
                class="cypher-input"
              />
            </div>

            <!-- Query History -->
            <div v-if="queryHistory.length > 0" class="query-history">
              <div class="history-title">查询历史</div>
              <div v-for="(h, i) in queryHistory.slice(0, 5)" :key="i" class="history-item" @click="cypherQuery = h.query; executeCypher()">
                <n-icon size="14"><time-outline /></n-icon>
                <span class="history-query">{{ truncate(h.query, 80) }}</span>
                <n-tag size="tiny" :bordered="false" :type="h.success ? 'success' : 'error'">{{ h.time }}</n-tag>
              </div>
            </div>

            <n-button type="primary" :loading="executing" @click="executeCypher" size="large">
              <template #icon><n-icon><play-outline /></n-icon></template>
              执行查询
            </n-button>
          </n-space>
        </n-tab-pane>

        <!-- Get Nodes Tab -->
        <n-tab-pane name="nodes" tab="📦 获取节点">
          <n-space :size="16" style="margin-bottom: 16px" align="end">
            <n-form-item label="标签 (可选)" style="margin-bottom:0">
              <n-input v-model:value="nodeLabel" placeholder="筛选标签" clearable style="width: 180px" />
            </n-form-item>
            <n-form-item label="数量限制" style="margin-bottom:0">
              <n-input-number v-model:value="nodeLimit" :min="1" :max="1000" style="width: 140px" />
            </n-form-item>
            <n-button type="primary" :loading="fetchingNodes" @click="fetchNodes">
              <template #icon><n-icon><search-outline /></n-icon></template>
              获取节点
            </n-button>
          </n-space>
        </n-tab-pane>

        <!-- Get Edges Tab -->
        <n-tab-pane name="edges" tab="🔗 获取关系">
          <n-space :size="16" style="margin-bottom: 16px" align="end">
            <n-form-item label="关系类型 (可选)" style="margin-bottom:0">
              <n-input v-model:value="relType" placeholder="筛选类型" clearable style="width: 180px" />
            </n-form-item>
            <n-form-item label="数量限制" style="margin-bottom:0">
              <n-input-number v-model:value="edgeLimit" :min="1" :max="1000" style="width: 140px" />
            </n-form-item>
            <n-button type="primary" :loading="fetchingEdges" @click="fetchEdges">
              <template #icon><n-icon><search-outline /></n-icon></template>
              获取关系
            </n-button>
          </n-space>
        </n-tab-pane>
      </n-tabs>

      <n-divider v-if="queryResult" />

      <!-- Results -->
      <transition name="fade-up">
        <div v-if="queryResult" class="query-result">
          <n-alert type="success" style="margin-bottom: 16px">
            <template #icon><n-icon><checkmark-circle-outline /></n-icon></template>
            查询成功 · {{ queryResult.length }} 条结果
          </n-alert>

          <n-tabs v-model:value="resultView" type="card" size="small">
            <n-tab-pane name="table" tab="📊 表格视图">
              <n-data-table :columns="resultColumns" :data="queryResult" :pagination="{ pageSize: 15 }" :scroll-x="1200" size="small" />
            </n-tab-pane>
            <n-tab-pane name="json" tab="📋 JSON 视图">
              <n-code :code="JSON.stringify(queryResult, null, 2)" language="json" />
            </n-tab-pane>
          </n-tabs>
        </div>
      </transition>
    </n-card>
  </div>
</template>

<script setup lang="ts">
/**
 * Query.vue - Cypher Query Interface View
 * Cypher 查询接口视图
 *
 * Purpose / 功能说明:
 *   Interactive query interface with three query modes:
 *   1. Cypher query - free-form MATCH/RETURN statements with templates and history
 *   2. Get Nodes - label-filtered node browsing
 *   3. Get Edges - relationship-type-filtered edge browsing
 *   Results are displayed as both a table (with auto-generated columns) and raw JSON.
 *   交互式查询界面，包含三种查询模式：
 *   1. Cypher 查询 - 使用模板和历史的自由格式 MATCH/RETURN 语句
 *   2. 获取节点 - 按标签筛选的节点浏览
 *   3. 获取关系 - 按关系类型筛选的边浏览
 *   结果以表格（自动生成列）和原始 JSON 两种视图展示。
 */
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMessage } from 'naive-ui'
import { PlayOutline, SearchOutline, TimeOutline, CheckmarkCircleOutline } from '@vicons/ionicons5'
import { executeCypherQuery, getNodes, getEdges } from '@/api/services'

const { t: _t } = useI18n()
const message = useMessage()

// ---- Reactive State / 响应式状态 ----

/** Currently active tab: "cypher" | "nodes" | "edges" / 当前激活的标签页 */
const activeTab = ref('cypher')

/** Cypher query text input / Cypher 查询文本输入 */
const cypherQuery = ref('')

/** Node label filter for the "Get Nodes" tab / "获取节点"标签页的标签筛选 */
const nodeLabel = ref('')
/** Node result limit for the "Get Nodes" tab / "获取节点"标签页的结果数量限制 */
const nodeLimit = ref(100)

/** Relationship type filter for the "Get Edges" tab / "获取关系"标签页的关系类型筛选 */
const relType = ref('')
/** Edge result limit for the "Get Edges" tab / "获取关系"标签页的结果数量限制 */
const edgeLimit = ref(100)

/** Whether a Cypher query is currently executing / Cypher 查询是否正在执行 */
const executing = ref(false)
/** Whether a "Get Nodes" request is in progress / 获取节点请求是否进行中 */
const fetchingNodes = ref(false)
/** Whether a "Get Edges" request is in progress / 获取关系请求是否进行中 */
const fetchingEdges = ref(false)

/** The query result data (shared across all three modes) / 查询结果数据（三种模式共享） */
const queryResult = ref<any>(null)
/** Active result view: "table" | "json" / 当前结果视图："table" | "json" */
const resultView = ref('table')

/** Type definition for a history entry / 历史记录条目的类型定义 */
interface HistoryItem { query: string; time: string; success: boolean }
/** List of past executed queries / 已执行的查询历史列表 */
const queryHistory = ref<HistoryItem[]>([])

/**
 * Pre-defined Cypher query templates for quick access.
 * 预定义的 Cypher 查询模板，方便快速使用。
 */
const cypherTemplates = [
  { label: '查看所有节点', query: 'MATCH (n) RETURN n LIMIT 25' },
  { label: '查看概念', query: 'MATCH (n:Concept) RETURN n LIMIT 25' },
  { label: '查看关系', query: 'MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 25' },
  { label: '统计标签', query: 'MATCH (n) RETURN labels(n) as label, count(n) as count ORDER BY count DESC' },
  { label: '统计关系', query: 'MATCH ()-[r]->() RETURN type(r) as type, count(r) as count ORDER BY count DESC' }
]

// ---- Utility Functions / 工具函数 ----

/**
 * Truncate a string to n characters with an ellipsis.
 * 将字符串截断到 n 个字符并添加省略号。
 */
const truncate = (s: string, n: number) => s.length > n ? s.slice(0, n) + '...' : s

/**
 * Clear all query history entries.
 * 清空所有查询历史记录。
 */
const clearHistory = () => { queryHistory.value = [] }

// ---- Computed / 计算属性 ----

/**
 * Auto-generate naive-ui data-table columns from the keys of the first result row.
 * Each column renders objects as JSON strings and nullish values as empty strings.
 * 从第一行结果对象的键自动生成 naive-ui 数据表列定义。
 * 对象类型的值会渲染为 JSON 字符串，空值渲染为空字符串。
 */
const resultColumns = computed(() => {
  if (!queryResult.value?.length) return []
  return Object.keys(queryResult.value[0]).map(key => ({
    title: key,
    key,
    ellipsis: { tooltip: true },
    render: (row: any) => {
      const v = row[key]
      return typeof v === 'object' ? JSON.stringify(v) : String(v ?? '')
    }
  }))
})

// ---- Query Functions / 查询函数 ----

/**
 * Execute the current Cypher query string via the API.
 * Records the result in the history (including success/failure state).
 * 通过 API 执行当前的 Cypher 查询语句。
 * 将结果记录到历史中（包括成功/失败状态）。
 */
const executeCypher = async () => {
  if (!cypherQuery.value.trim()) { message.warning('请输入查询语句'); return }
  executing.value = true
  try {
    const result = await executeCypherQuery(cypherQuery.value)
    if (Array.isArray(result) && result.length > 0) {
      queryResult.value = result
      queryHistory.value.unshift({ query: cypherQuery.value, time: new Date().toLocaleTimeString(), success: true })
      message.success(`查询成功，${result.length} 条结果`)
    } else {
      queryResult.value = null
      queryHistory.value.unshift({ query: cypherQuery.value, time: new Date().toLocaleTimeString(), success: false })
      message.warning('无结果')
    }
  } catch (error: any) {
    message.error('查询失败: ' + error.message)
    queryHistory.value.unshift({ query: cypherQuery.value, time: new Date().toLocaleTimeString(), success: false })
    queryResult.value = null
  } finally { executing.value = false }
}

/**
 * Fetch nodes from the API, optionally filtered by label and limited in count.
 * 从 API 获取节点，可按标签筛选并限制数量。
 */
const fetchNodes = async () => {
  fetchingNodes.value = true
  try {
    const result = await getNodes(nodeLabel.value || null, nodeLimit.value)
    if (Array.isArray(result) && result.length > 0) {
      queryResult.value = result
      message.success(`找到 ${result.length} 个节点`)
    } else { message.warning('未找到节点'); queryResult.value = null }
  } catch (error: any) { message.error('获取失败: ' + error.message); queryResult.value = null }
  finally { fetchingNodes.value = false }
}

/**
 * Fetch edges from the API, optionally filtered by relationship type and limited in count.
 * 从 API 获取关系，可按关系类型筛选并限制数量。
 */
const fetchEdges = async () => {
  fetchingEdges.value = true
  try {
    const result = await getEdges(relType.value || null, edgeLimit.value)
    if (Array.isArray(result) && result.length > 0) {
      queryResult.value = result
      message.success(`找到 ${result.length} 个关系`)
    } else { message.warning('未找到关系'); queryResult.value = null }
  } catch (error: any) { message.error('获取失败: ' + error.message); queryResult.value = null }
  finally { fetchingEdges.value = false }
}
</script>

<style lang="scss" scoped>
.query-page {
  padding: 28px 40px;
  min-height: calc(100vh - 64px);
  position: relative;

  .page-bg {
    position: fixed; inset: 0;
    background:
      radial-gradient(ellipse at 20% 20%, rgba(59, 130, 246, 0.05) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 80%, rgba(96, 165, 250, 0.05) 0%, transparent 50%);
    pointer-events: none; z-index: 0;
  }

  > * { position: relative; z-index: 1; }
}

.query-header {
  margin-bottom: 24px; padding: 24px 32px;

  .query-title { font-size: 32px; font-weight: 800; margin: 0 0 6px; letter-spacing: -0.5px; }
  .query-subtitle { font-size: 14px; color: var(--color-text-muted); margin: 0; }
}

.query-card {
  :deep(.n-card__content) { padding: 24px; }
}

// Cypher input
.cypher-input-wrapper {
  border-radius: var(--radius-xl);
  overflow: hidden;
  border: 1px solid rgba(59, 130, 246, 0.15);
  background: rgba(255,255,255,0.6);

  .cypher-toolbar {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 14px; background: rgba(59,130,246,0.04);
    border-bottom: 1px solid rgba(59,130,246,0.08);
  }
}

.cypher-input {
  :deep(textarea) {
    font-family: var(--font-mono) !important;
    font-size: 14px !important;
    line-height: 1.7 !important;
    border: none !important;
    border-radius: 0 !important;
    background: transparent !important;
    padding: 14px 16px !important;
  }
}

// Query history
.query-history {
  padding: 12px; border-radius: var(--radius-lg);
  background: rgba(255,255,255,0.6); border: 1px solid rgba(59,130,246,0.1);

  .history-title { font-size: 12px; font-weight: 700; color: var(--color-text-muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
  .history-item {
    display: flex; align-items: center; gap: 8px;
    padding: 6px 10px; border-radius: var(--radius-sm);
    cursor: pointer; transition: all var(--transition-fast);
    border: 1px solid transparent;

    &:hover { background: rgba(59,130,246,0.06); border-color: rgba(59,130,246,0.15); }
    .history-query { flex: 1; font-size: 12px; font-family: var(--font-mono); color: var(--color-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  }
}

// Results
.query-result {
  margin-top: 20px;

  :deep(.n-alert) { border-radius: var(--radius-lg); font-weight: 600; }

  :deep(.n-data-table) {
    border-radius: var(--radius-lg); overflow: hidden;
    .n-data-table-th { background: linear-gradient(135deg, rgba(59,130,246,0.06), rgba(96,165,250,0.04)); font-weight: 700; text-transform: uppercase; font-size: 12px; }
  }

  :deep(.n-code) {
    border-radius: var(--radius-lg);
    background: linear-gradient(135deg, rgba(15,23,42,0.98), rgba(30,41,59,0.98));
    padding: 20px; font-size: 13px;
  }
}

// Tabs
:deep(.n-tabs) {
  .n-tabs-nav {
    background: linear-gradient(135deg, rgba(248,250,252,0.8), rgba(241,245,249,0.8));
    border-radius: var(--radius-lg); padding: 6px; margin-bottom: 20px;
  }
  .n-tabs-tab {
    font-weight: 700; padding: 12px 20px; border-radius: var(--radius-md);
    transition: all var(--transition-base);
    &.n-tabs-tab--active {
      background: linear-gradient(135deg, #fff, #f8fafc);
      box-shadow: var(--shadow-sm);
    }
  }
}

:deep(.n-button--primary-type) { box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25); border-radius: var(--radius-md) !important; }

// Animations
.fade-up-enter-active { transition: all 0.5s ease-out; }
.fade-up-leave-active { transition: all 0.2s ease-in; }
.fade-up-enter-from { opacity: 0; transform: translateY(30px); }
.fade-up-leave-to { opacity: 0; transform: translateY(-10px); }
</style>
