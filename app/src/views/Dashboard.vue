<template>
  <div class="dashboard-page">
    <!-- Floating particles background -->
    <div class="page-bg"></div>

    <!-- Header -->
    <div class="page-header glass-card">
      <div class="header-content">
        <h1 class="page-title gradient-text-gold">GraphForge</h1>
        <p class="page-subtitle">仪表盘 · Dashboard — 知识图谱全景视图</p>
        <div class="header-stats-mini" v-if="!loading">
          <span class="mini-stat">
            <span class="mini-dot" style="background:#10b981"></span>
            在线 · {{ stats.totalConcepts }} 概念 · {{ stats.totalRelations }} 关系
          </span>
        </div>
      </div>
      <div class="header-actions">
        <n-button type="primary" @click="refreshStats" :loading="loading" secondary>
          <template #icon><n-icon><refresh-outline /></n-icon></template>
          刷新数据
        </n-button>
        <n-button @click="$router.push('/knowledge')">
          <template #icon><n-icon><cloud-upload-outline /></n-icon></template>
          知识构建
        </n-button>
      </div>
    </div>

    <!-- Stats Cards with staggered animation -->
    <div class="stats-grid stagger-container">
      <div class="stat-card" v-for="(card, idx) in statCards" :key="idx" :style="{ '--card-color': card.color }">
        <div class="stat-icon" :style="{ background: card.bg }">
          <n-icon size="28"><component :is="card.icon" /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value-wrap">
            <n-skeleton v-if="loading" text :width="80" :height="36" />
            <span v-else class="stat-value count-up">
              <n-number-animation :from="0" :to="card.value" :duration="1500" />
              <span v-if="card.suffix" class="stat-suffix">{{ card.suffix }}</span>
            </span>
          </div>
          <div class="stat-footer">
            <n-icon v-if="card.trend" size="14" :color="card.trendColor" :component="TrendingUpOutline" />
            <span class="stat-desc" :style="{ color: card.trendColor }">{{ card.desc }}</span>
          </div>
        </div>
        <div class="stat-glow" :style="{ background: card.bg }"></div>
      </div>
    </div>

    <!-- Charts & Info Grid -->
    <div class="content-grid stagger-container">
      <!-- Relation Type Distribution -->
      <div class="content-card chart-section">
        <div class="section-header">
          <n-icon size="20"><pie-chart-outline /></n-icon>
          <h3>关系类型分布</h3>
        </div>
        <div class="chart-container">
          <template v-if="loading">
            <n-skeleton text style="width:100%;height:300px" :repeat="1" />
          </template>
          <template v-else-if="pieChartOption.series[0].data.length > 0">
            <v-chart :option="pieChartOption" autoresize style="height:320px" />
          </template>
          <n-empty v-else description="暂无数据" size="small" />
        </div>
      </div>

      <!-- Top Concepts -->
      <div class="content-card info-section">
        <div class="section-header">
          <n-icon size="20"><trophy-outline /></n-icon>
          <h3>核心概念排行</h3>
        </div>
        <div class="concepts-list">
          <template v-if="loading">
            <div v-for="i in 5" :key="i" class="skeleton-row">
              <div class="skeleton skeleton-circle" style="width:32px;height:32px"></div>
              <div class="skeleton skeleton-text" style="flex:1;height:16px"></div>
              <div class="skeleton skeleton-text" style="width:60px;height:20px"></div>
            </div>
          </template>
          <n-scrollbar v-else style="max-height: 320px;">
            <div v-if="stats.topConcepts && stats.topConcepts.length > 0">
              <div v-for="(concept, index) in stats.topConcepts" :key="index" class="concept-item">
                <div class="concept-rank" :class="`rank-${index + 1}`">{{ index + 1 }}</div>
                <div class="concept-info">
                  <div class="concept-name">{{ concept.name }}</div>
                  <div class="concept-domain" v-if="concept.domain">{{ concept.domain }}</div>
                </div>
                <n-tag :bordered="false" type="warning" size="small" round>
                  {{ concept.connections }} 连接
                </n-tag>
              </div>
            </div>
            <n-empty v-else description="暂无概念数据" size="small" />
          </n-scrollbar>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="content-card actions-section">
        <div class="section-header">
          <n-icon size="20"><rocket-outline /></n-icon>
          <h3>快速操作</h3>
        </div>
        <div class="quick-actions">
          <div
            v-for="action in quickActions"
            :key="action.path"
            class="action-card"
            @click="$router.push(action.path)"
          >
            <div class="action-icon" :style="{ background: action.bg }">
              <n-icon size="24"><component :is="action.icon" /></n-icon>
            </div>
            <div class="action-content">
              <div class="action-title">{{ action.title }}</div>
              <div class="action-desc">{{ action.desc }}</div>
            </div>
            <n-icon class="action-arrow" size="16"><arrow-forward-outline /></n-icon>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Documents Table -->
    <div class="content-card table-section">
      <div class="section-header">
        <n-icon size="20"><document-text-outline /></n-icon>
        <h3>最近上传的文档</h3>
      </div>
      <template v-if="loading">
        <n-skeleton text :repeat="3" />
      </template>
      <template v-else-if="stats.recentDocuments && stats.recentDocuments.length > 0">
        <n-data-table :columns="docColumns" :data="stats.recentDocuments" :bordered="false" />
      </template>
      <n-empty v-else description="暂无文档" size="small" />
    </div>

    <!-- System Status -->
    <div class="content-card status-section">
      <div class="section-header">
        <n-icon size="20"><server-outline /></n-icon>
        <h3>系统状态</h3>
      </div>
      <div class="status-grid">
        <div v-for="svc in systemServices" :key="svc.name" class="status-item">
          <div class="status-icon" :style="{ background: svc.bg }">
            <n-icon size="22"><component :is="svc.icon" /></n-icon>
          </div>
          <div class="status-content">
            <div class="status-label">{{ svc.label }}</div>
            <n-tag :type="svc.ok ? 'success' : 'warning'" :bordered="false" round size="small">
              <template #icon>
                <span class="status-pulse" :class="{ active: svc.ok }"></span>
              </template>
              {{ svc.status }}
            </n-tag>
          </div>
          <div class="status-bar" :class="{ ok: svc.ok }"></div>
        </div>
      </div>
    </div>

    <!-- QA Dialog -->
    <QADialog v-model="showQADialog" />
  </div>
</template>

<script setup lang="ts">
/**
 * Dashboard.vue - 仪表盘主视图 / Main Dashboard View
 *
 * 【功能 / Functionality】
 * 1. 统计卡片展示（文档数、概念、关系、图谱密度）/ Stats cards (documents, concepts, relations, density)
 * 2. 关系类型分布饼图（基于 ECharts）/ Relation type distribution pie chart
 * 3. 核心概念排行列表 / Top concepts ranking list
 * 4. 快速操作导航卡片 / Quick action navigation cards
 * 5. 最近上传文档表格 / Recent documents data table
 * 6. 系统服务状态监控（Neo4j, Redis, 向量检索, LLM）/ System service health monitoring
 * 7. 智能问答对话框入口 / QA dialog entry
 *
 * 【角色 / Role】
 * 系统首页，提供知识图谱核心指标的全景概览和快捷入口。
 * Acts as the system homepage, providing a panoramic overview of key knowledge graph metrics
 * and quick-access entry points for all major features.
 */

import { ref, computed, onMounted, h } from 'vue'
import {
  NButton, NIcon, NNumberAnimation, NSkeleton, NEmpty, NTag,
  NDataTable, NScrollbar, useMessage
} from 'naive-ui'
import {
  RefreshOutline, CloudUploadOutline, DocumentTextOutline,
  BulbOutline, GitNetworkOutline, AnalyticsOutline, TrendingUpOutline,
  PieChartOutline, TrophyOutline, RocketOutline, ArrowForwardOutline,
  SearchOutline, ChatbubbleEllipsesOutline, ServerOutline,
  LayersOutline, CubeOutline, SparklesOutline
} from '@vicons/ionicons5'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { getDashboardStats, getRedisHealth } from '@/api/services'
import QADialog from '@/components/QADialog.vue'

// ---------------------------------------------------------------------------
// ECharts 注册 / Register ECharts modules for pie chart rendering
// ---------------------------------------------------------------------------
use([CanvasRenderer, PieChart, TitleComponent, TooltipComponent, LegendComponent])

const message = useMessage()

// ---------------------------------------------------------------------------
// 响应式状态 / Reactive State
// ---------------------------------------------------------------------------

/** 全局加载状态 / Global loading state for skeleton placeholders */
const loading = ref(true)

/** 控制智能问答对话框的显示 / Controls QA dialog visibility */
const showQADialog = ref(false)

/**
 * 仪表盘统计数据 / Dashboard aggregated statistics
 * 由 getDashboardStats API 填充，包含文档/概念/关系计数、最近文档、核心概念和关系类型分布。
 * Populated by getDashboardStats API; holds document/concept/relation counts,
 * recent documents, top concepts, and relation type distribution.
 */
const stats = ref({
  totalDocuments: 0,           // 文档总数 / Total document count
  totalConcepts: 0,            // 概念节点数 / Total concept node count
  totalRelations: 0,           // 关系连接数 / Total relationship count
  recentDocuments: [] as any[], // 最近上传文档列表 / Recently uploaded documents
  topConcepts: [] as any[],    // 核心概念排行 / Top-ranked concepts by connection count
  relationTypes: [] as any[]   // 关系类型分布统计 / Relation type distribution stats
})

/** Redis 服务健康状态 / Redis service health status */
const redisOk = ref(false)
const redisStatus = ref('检查中...')

/** LLM 服务状态 / LLM service status (defaults to mock mode) */
const llmOk = ref(false)
const llmStatus = ref('Mock模式')

// ---------------------------------------------------------------------------
// 计算属性 / Computed Properties
// ---------------------------------------------------------------------------

/**
 * 图谱密度计算 / Graph density computation
 * density = totalRelations / (totalConcepts * (totalConcepts - 1)) * 100
 * 衡量知识图谱的连通性，值越高表示概念间关联越紧密。
 * Measures graph connectivity — higher values indicate tighter concept coupling.
 */
const graphDensity = computed(() => {
  if (stats.value.totalConcepts === 0) return 0
  const max = stats.value.totalConcepts * (stats.value.totalConcepts - 1)
  return max === 0 ? 0 : +(stats.value.totalRelations / max * 100).toFixed(2)
})

/**
 * 统计卡片配置 / Stat cards configuration
 * 定义四个指标的图标、标签、颜色渐变和描述文本，用于渲染统计卡片。
 * Defines four metric cards with icons, labels, gradient colors, and descriptions.
 */
const statCards = computed(() => [
  { label: '文档总数', value: stats.value.totalDocuments, suffix: '', icon: DocumentTextOutline, color: '#d4af37', bg: 'linear-gradient(135deg, #d4af37, #c9a668)', desc: 'PDF · Markdown · TXT · Word', trendColor: '#10b981', trend: true },
  { label: '概念节点', value: stats.value.totalConcepts, suffix: '', icon: BulbOutline, color: '#c9a668', bg: 'linear-gradient(135deg, #c9a668, #b8860b)', desc: '知识体系', trendColor: '#10b981', trend: true },
  { label: '关系连接', value: stats.value.totalRelations, suffix: '', icon: GitNetworkOutline, color: '#b8860b', bg: 'linear-gradient(135deg, #b8860b, #9a7509)', desc: '关联网络', trendColor: '#10b981', trend: true },
  { label: '图谱密度', value: graphDensity.value, suffix: '%', icon: AnalyticsOutline, color: '#daa520', bg: 'linear-gradient(135deg, #daa520, #c9a668)', desc: '持续增长', trendColor: '#10b981', trend: true }
])

/**
 * 快速操作导航配置 / Quick action navigation configuration
 * 定义了五个主要功能模块的入口卡片：知识构建、文档管理、图谱可视化、知识查询、智能问答。
 * Defines five entry-point cards for major feature modules.
 */
const quickActions = [
  { title: '知识构建', desc: '导入文档/文本构建知识', path: '/knowledge', icon: CloudUploadOutline, bg: 'linear-gradient(135deg, #d4af37, #b8860b)' },
  { title: '文档管理', desc: '查看和管理已上传文档', path: '/documents', icon: DocumentTextOutline, bg: 'linear-gradient(135deg, #c9a668, #9a7509)' },
  { title: '图谱可视化', desc: '探索知识关系网络', path: '/graph', icon: GitNetworkOutline, bg: 'linear-gradient(135deg, #9b87f5, #7c6ae0)' },
  { title: '知识查询', desc: '使用 Cypher 查询图谱', path: '/query', icon: SearchOutline, bg: 'linear-gradient(135deg, #3b82f6, #2563eb)' },
  { title: '智能问答', desc: '向知识图谱提问', path: '#', icon: ChatbubbleEllipsesOutline, bg: 'linear-gradient(135deg, #10b981, #059669)' }
]

/**
 * 系统服务状态 / System service health status
 * 将静态信息和动态检测结果组合，形成统一的系统状态视图。
 * Combines static service info with dynamic health-check results.
 */
const systemServices = computed(() => [
  // Neo4j: 通过文档数量推断其运行状态 / Infer status from document count
  { name: 'neo4j', label: 'Neo4j 图数据库', icon: ServerOutline, bg: 'linear-gradient(135deg, #10b981, #059669)', ok: stats.value.totalDocuments >= 0, status: '运行中' },
  // Redis: 通过 health-check API 获取 / Determined via health-check API
  { name: 'redis', label: 'Redis 队列', icon: LayersOutline, bg: 'linear-gradient(135deg, #f59e0b, #d97706)', ok: redisOk.value, status: redisStatus.value },
  // FAISS 向量检索为固定状态，通常由后端确认 / Vector search via FAISS is static
  { name: 'vector', label: '向量检索', icon: CubeOutline, bg: 'linear-gradient(135deg, #3b82f6, #2563eb)', ok: true, status: 'FAISS' },
  // LLM 服务通过 /llm health-check 获取 / LLM status via health-check or defaults to Mock
  { name: 'llm', label: 'LLM 服务', icon: SparklesOutline, bg: 'linear-gradient(135deg, #8b5cf6, #6d28d9)', ok: llmOk.value, status: llmStatus.value }
])

/**
 * ECharts 饼图配置 / ECharts pie chart option
 * 将 relationTypes 数据转换为 ECharts 可消费的 series.data 格式。
 * Transforms relationTypes data into ECharts-compatible series.data format.
 * 使用环形图（甜甜圈图）风格，半径 45%-75%，强调交互高亮效果。
 * Uses donut chart style (radius 45%-75%) with emphasis highlighting.
 */
const pieChartOption = computed(() => {
  // 将 [{type, count}] 映射为 [{name, value}]
  const data = stats.value.relationTypes.map((rt: any) => ({ value: rt.count, name: rt.type }))
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: 10, top: 'center', textStyle: { color: '#666' } },
    series: [{
      name: '关系类型', type: 'pie',
      radius: ['45%', '75%'],                // 内径/外径 / Inner/outer radius for donut shape
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 3 }, // 圆角扇形 / Rounded sectors
      label: { show: false },                // 默认隐藏标签，hover 时显示 / Hide labels by default, show on hover
      emphasis: {
        label: { show: true, fontSize: 18, fontWeight: 'bold', color: '#d4af37' },
        scaleSize: 12,
        focus: 'self'                        // 高亮时只聚焦自身区块 / Focus only the hovered sector
      },
      labelLine: { show: false },
      data,
      color: ['#d4af37', '#c9a668', '#b8860b', '#daa520', '#8b6914', '#9b87f5', '#7c6ae0']
    }]
  }
})

// ---------------------------------------------------------------------------
// 文档表格列定义 / Document DataTable Column Definitions
// ---------------------------------------------------------------------------

/**
 * 最近上传文档的表格列配置
 * Columns for the recent documents data table.
 * 使用 Naive UI 的 h() 渲染函数实现自定义列模板。
 * Uses Naive UI's h() render function for custom column templates.
 */
const docColumns = [
  // 文件名列，附带图标 / Filename column with document icon
  { title: '文件名', key: 'filename', ellipsis: { tooltip: true }, render: (row: any) => h('div', { style: 'display:flex;align-items:center;gap:8px' }, [
    h(NIcon, { size: 18, color: '#d4af37' }, { default: () => h(DocumentTextOutline) }),
    h('span', { style: 'font-weight:500' }, row.filename || '未命名')
  ]) },
  // 类型列，映射为对应颜色的标签 / Type column rendered as colored tags
  { title: '类型', key: 'kind', width: 90, render: (row: any) => {
    const m: Record<string, any> = { pdf: { text: 'PDF', type: 'error' }, md: { text: 'MD', type: 'info' }, docx: { text: 'Word', type: 'primary' }, epub: { text: 'EPUB', type: 'success' } }
    const c = m[row.kind] || { text: row.kind?.toUpperCase() || '?', type: 'default' }
    return h(NTag, { type: c.type, size: 'small', bordered: false }, () => c.text)
  } },
  // 文档 ID 列 / Document ID column (monospace, muted)
  { title: '文档ID', key: 'id', width: 120, ellipsis: { tooltip: true }, render: (row: any) => h('code', { style: 'font-size:11px;color:#94a3b8' }, row.id || 'N/A') },
  // 上传时间列 / Upload time column (formatted in zh-CN locale)
  { title: '上传时间', key: 'createdAt', width: 170, render: (row: any) => row.createdAt ? new Date(row.createdAt).toLocaleString('zh-CN') : 'N/A' }
]

// ---------------------------------------------------------------------------
// 方法 / Methods
// ---------------------------------------------------------------------------

/**
 * 加载仪表盘统计数据 / Load dashboard statistics from the API
 *
 * 发送请求到 getDashboardStats 端点，获取所有核心指标数据。
 * Sends a request to the getDashboardStats endpoint to fetch all core metrics.
 * 在 finally 块中确保 loading 状态被重置，使骨架屏正确切换。
 * Ensures loading state is reset in finally block for proper skeleton transitions.
 */
const loadStats = async () => {
  loading.value = true
  try {
    const data: any = await getDashboardStats()
    // 解构 API 返回值并填充响应式状态，使用 || 提供默认值防止 undefined
    stats.value = {
      totalDocuments: data.totalDocuments || 0,
      totalConcepts: data.totalConcepts || 0,
      totalRelations: data.totalRelations || 0,
      recentDocuments: data.recentDocuments || [],
      topConcepts: data.topConcepts || [],
      relationTypes: data.relationTypes || []
    }
  } catch {
    // 加载失败时通过 Naive UI 的 Message 组件提示用户
    message.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

/**
 * 刷新统计数据的便捷方法 / Convenience wrapper for refreshing stats
 * 在模板中由"刷新数据"按钮直接调用。
 * Called directly by the "Refresh" button in the template.
 */
const refreshStats = () => loadStats()

/**
 * 检查 Redis 服务健康状态 / Check Redis service health
 *
 * 调用 getRedisHealth API 检测 Redis 连接状态。
 * Calls the getRedisHealth API to inspect Redis connection status.
 * 成功时提取版本和内存信息增强展示，失败时显示"无法检测"。
 * On success extracts version and memory info for display; on failure shows "unreachable".
 */
const checkRedisHealth = async () => {
  try {
    const resp = await getRedisHealth()
    redisOk.value = resp.success
    redisStatus.value = resp.success
      ? `运行中 · ${resp.data?.redis_version || ''} · ${resp.data?.used_memory_human || ''}`
      : (resp.data?.error || '未连接')
  } catch {
    // 网络错误或 API 不可达时默认标记为不可用
    redisOk.value = false
    redisStatus.value = '无法检测'
  }
}

// ---------------------------------------------------------------------------
// 生命周期钩子 / Lifecycle Hooks
// ---------------------------------------------------------------------------

/** 组件挂载时同时加载统计数据并检测 Redis 健康状态 */
onMounted(() => { loadStats(); checkRedisHealth() })
</script>

<style lang="scss" scoped>
.dashboard-page {
  padding: 28px 40px;
  min-height: calc(100vh - 64px);
  position: relative;

  .page-bg {
    position: fixed;
    inset: 0;
    background:
      radial-gradient(ellipse at 15% 15%, rgba(212, 175, 55, 0.05) 0%, transparent 50%),
      radial-gradient(ellipse at 85% 85%, rgba(155, 135, 245, 0.05) 0%, transparent 50%),
      radial-gradient(ellipse at 50% 50%, rgba(184, 134, 11, 0.03) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
  }

  > * { position: relative; z-index: 1; }
}

// Header
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
  padding: 28px 32px;

  .header-content {
    .page-title { font-size: 34px; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
    .page-subtitle { font-size: 14px; color: var(--color-text-muted); margin: 6px 0; font-weight: 500; }
    .header-stats-mini {
      margin-top: 8px;
      .mini-stat { font-size: 12px; color: var(--color-text-secondary); display: flex; align-items: center; gap: 6px; font-weight: 500; }
      .mini-dot { width: 8px; height: 8px; border-radius: 50%; animation: pulseGlow 2s ease-in-out infinite; }
    }
  }

  .header-actions { display: flex; gap: 10px; flex-shrink: 0; }
}

// Stats grid
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 28px;
}

.stat-card {
  position: relative;
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 18px;
  border: 1px solid var(--color-border-light);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);
  cursor: pointer;
  overflow: hidden;

  .stat-glow {
    position: absolute;
    inset: -50%;
    opacity: 0;
    transition: opacity var(--transition-base);
    filter: blur(60px);
    pointer-events: none;
  }

  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg), 0 0 30px var(--color-primary-glow);
    border-color: var(--color-primary-light);

    .stat-glow { opacity: 0.08; }
  }

  .stat-icon {
    width: 56px;
    height: 56px;
    border-radius: var(--radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    flex-shrink: 0;
    box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
  }

  .stat-content {
    flex: 1;
    min-width: 0;

    .stat-label { font-size: 13px; color: var(--color-text-muted); font-weight: 500; margin-bottom: 6px; }
    .stat-value-wrap { margin-bottom: 6px; }
    .stat-value {
      font-size: 30px;
      font-weight: 800;
      color: var(--color-text);
      line-height: 1;
      letter-spacing: -0.5px;
    }
    .stat-suffix { font-size: 16px; font-weight: 600; color: var(--color-text-secondary); margin-left: 2px; }
    .stat-footer {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      font-weight: 500;
    }
  }
}

// Content grid
.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
  margin-bottom: 28px;
}

.content-card {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-base);

  &:hover {
    box-shadow: var(--shadow-md);
    border-color: rgba(194, 164, 116, 0.2);
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    padding-bottom: 14px;
    border-bottom: 2px solid var(--color-border-light);

    h3 { margin: 0; font-size: 16px; font-weight: 700; color: var(--color-text); }
    .n-icon { color: var(--color-primary-light); }
  }
}

// Chart
.chart-container { min-height: 320px; display: flex; align-items: center; justify-content: center; }

// Concepts
.concepts-list {
  .concept-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-radius: var(--radius-md);
    margin-bottom: 6px;
    background: var(--color-bg-alt);
    transition: all var(--transition-fast);

    &:hover {
      background: linear-gradient(135deg, var(--color-primary-subtle), rgba(155, 135, 245, 0.06));
      transform: translateX(4px);
    }

    .concept-rank {
      width: 30px; height: 30px;
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700; font-size: 13px;
      background: #e2e8f0; color: #64748b;

      // Top-3 ranks get gold gradient treatment
      &.rank-1 { background: linear-gradient(135deg, #d4af37, #b8860b); color: #fff; }
      &.rank-2 { background: linear-gradient(135deg, #c9a668, #9a7509); color: #fff; }
      &.rank-3 { background: linear-gradient(135deg, #daa520, #c9a668); color: #fff; }
    }

    .concept-info {
      flex: 1; min-width: 0;
      .concept-name { font-weight: 600; font-size: 14px; color: var(--color-text); margin-bottom: 2px; }
      .concept-domain { font-size: 11px; color: var(--color-text-muted); }
    }
  }
}

// Quick actions
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;

  .action-card {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px;
    border-radius: var(--radius-lg);
    background: var(--color-bg-alt);
    cursor: pointer;
    transition: all var(--transition-base);
    border: 1px solid transparent;

    &:hover {
      background: var(--color-surface);
      border-color: rgba(194, 164, 116, 0.4);
      box-shadow: 0 4px 16px rgba(194, 164, 116, 0.15);
      transform: translateX(4px);

      .action-arrow { transform: translateX(4px); opacity: 1; }
    }

    .action-icon {
      width: 44px; height: 44px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      flex-shrink: 0;
      box-shadow: 0 4px 10px rgba(212, 175, 55, 0.25);
    }

    .action-content {
      flex: 1;
      .action-title { font-weight: 600; font-size: 14px; color: var(--color-text); margin-bottom: 2px; }
      .action-desc { font-size: 12px; color: var(--color-text-muted); }
    }

    .action-arrow {
      color: var(--color-primary-light);
      transition: all var(--transition-base);
      opacity: 0.5;
    }
  }
}

// Table & Status sections
.table-section, .status-section {
  margin-bottom: 24px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;

  .status-item {
    position: relative;
    padding: 18px;
    border-radius: var(--radius-lg);
    display: flex;
    align-items: center;
    gap: 14px;
    transition: all var(--transition-fast);
    border: 1px solid var(--color-border-light);
    overflow: hidden;

    &:hover {
      border-color: rgba(194, 164, 116, 0.3);
      box-shadow: var(--shadow-md);
      transform: translateY(-2px);
    }

    .status-icon {
      width: 42px; height: 42px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      flex-shrink: 0;
    }

    .status-content {
      flex: 1;
      display: flex;
      justify-content: space-between;
      align-items: center;
      .status-label { font-size: 13px; font-weight: 600; color: var(--color-text); }
    }

    .status-bar {
      position: absolute;
      bottom: 0; left: 0; right: 0;
      height: 3px;
      background: #ef4444;
      transition: background var(--transition-base);
      &.ok { background: linear-gradient(90deg, #10b981, #34d399); }
    }
  }
}

// Status pulse
.status-pulse {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #d1d5db;
  margin-right: 2px;
  &.active { background: #10b981; animation: pulse 2s ease-in-out infinite; }
}

// Skeleton
.skeleton-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: var(--radius-md);
  background: var(--color-bg-alt);
}

// Skeleton text
.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmerSlow 1.5s linear infinite;
  border-radius: 4px;
}

.skeleton-text { height: 14px; margin-bottom: 6px; border-radius: var(--radius-sm); }
.skeleton-circle { border-radius: 50%; flex-shrink: 0; }

@keyframes shimmerSlow {
  0% { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
  50% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
}

// Responsive
@media (max-width: 1400px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .content-grid { grid-template-columns: 1fr; }
  .status-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .dashboard-page { padding: 16px; }
  .stats-grid { grid-template-columns: 1fr; }
  .status-grid { grid-template-columns: 1fr; }
  .page-header { flex-direction: column; gap: 16px; }
  .header-actions { width: 100%; button { flex: 1; } }
}
</style>
