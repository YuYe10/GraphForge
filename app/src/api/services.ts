/**
 * GraphForge API Service Layer
 * =============================
 *
 * Type-safe service functions and interfaces for the GraphForge backend API.
 * Each function wraps an Axios call to a specific FastAPI endpoint, providing
 * typed parameters and return values for the frontend UI components.
 *
 * Sections / 章节:
 *   - Exports           - Re-exported constants
 *   - Shared Types      - Common interfaces used across services
 *   - Dashboard         - Statistics overview
 *   - Upload            - Document/file/URL ingestion
 *   - Documents         - Document CRUD and detail queries
 *   - Graph             - Graph data retrieval for visualization
 *   - Query             - Cypher and entity queries
 *   - Job Status        - Ingestion progress polling
 *   - Settings          - AI provider & system configuration
 *   - Graph CRUD        - Node / Edge create, read, update, delete
 *   - Q&A               - Question-answering against the knowledge graph
 *
 * GraphForge 后端 API 服务层
 * 提供类型安全的函数与接口封装，每个函数对应一个 FastAPI 端点。
 */

import api from './index'

// ===========================================================================
// Exports / 模块导出
// ===========================================================================

/**
 * Backend API base URL, re-exported so consumers can construct absolute URLs
 * (e.g., file download/preview links) without re-reading environment variables.
 *
 * 后端 API 基础地址，重新导出以供构造绝对 URL（如文件下载/预览链接）。
 */
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// ===========================================================================
// Shared Types / 共享类型定义
// ===========================================================================

/**
 * Dashboard statistics returned by the backend.
 * 仪表盘统计数据，反映知识图谱的整体规模与构成。
 */
export interface DashboardStats {
  /** Total number of nodes in the graph / 图谱中的节点总数 */
  total_nodes: number
  /** Total number of edges (relationships) in the graph / 图谱中的边（关系）总数 */
  total_edges: number
  /** Per-label node count, e.g. { "Person": 42, "Company": 15 } / 按标签统计的节点数量 */
  node_labels: Record<string, number>
  /** Per-type edge count, e.g. { "WORKS_AT": 30 } / 按类型统计的边数量 */
  edge_types: Record<string, number>
}

/**
 * Response returned after a file, text, or URL upload.
 * 文件、文本或 URL 上传后返回的响应结构。
 */
export interface UploadResponse {
  /** Unique document identifier / 文档唯一标识 */
  documentId: string
  /** Original filename / 原始文件名 */
  filename: string
  /** MD5/SHA checksum for integrity verification / 文件校验和 */
  checksum: string
  /** Processing status (e.g., pending, processing, completed, failed) / 处理状态 */
  status: string
  /** Job ID for tracking ingestion progress (if auto-processing) / 导入任务 ID（自动处理时） */
  jobId?: string
  /** Human-readable status message / 可读的状态信息 */
  message?: string
  /** Server-side file storage path / 服务端文件存储路径 */
  path?: string
  /** Source URL for URL-based uploads / URL 上传的源地址 */
  sourceUrl?: string
}

/**
 * Response from starting a background ingestion job.
 * 启动后台导入任务后返回的响应。
 */
export interface IngestionResponse {
  /** Unique job identifier for status polling / 任务唯一标识，用于轮询状态 */
  job_id: string
  /** Initial job status / 任务初始状态 */
  status: string
}

/**
 * A single node in the knowledge graph.
 * 知识图谱中的单个节点。
 */
export interface GraphNode {
  /** Neo4j internal node ID / Neo4j 内部节点 ID */
  id: string
  /** Node labels (e.g., ["Person", "Researcher"]) / 节点标签 */
  labels: string[]
  /** Key-value property map / 键值属性映射 */
  properties: Record<string, any>
}

/**
 * A single directed edge (relationship) in the knowledge graph.
 * 知识图谱中的单条有向边（关系）。
 */
export interface GraphEdge {
  /** Neo4j internal relationship ID / Neo4j 内部关系 ID */
  id: string
  /** Relationship type (e.g., "WORKS_AT", "CITES") / 关系类型 */
  type: string
  /** Source node ID / 起始节点 ID */
  source: string
  /** Target node ID / 目标节点 ID */
  target: string
  /** Key-value property map / 键值属性映射 */
  properties: Record<string, any>
}

/**
 * Graph data payload containing both nodes and edges.
 * 包含节点与边的图谱数据载荷。
 */
export interface GraphData {
  /** All nodes in the current view / 当前视图中的所有节点 */
  nodes: GraphNode[]
  /** All edges (relationships) in the current view / 当前视图中的所有边 */
  edges: GraphEdge[]
}

/**
 * Status of a document ingestion job, used for progress polling.
 * 文档导入任务的状态，用于前端轮询进度。
 */
export interface JobStatus {
  /** Job identifier / 任务 ID */
  jobId?: string
  /** Associated document identifier / 关联的文档 ID */
  documentId?: string
  /** Current status: pending | processing | completed | failed / 当前状态 */
  status: string
  /** Processing progress as a percentage (0-100) / 处理进度百分比 */
  progress?: number
  /** Human-readable status description / 可读的状态描述 */
  message?: string
  /** Error details if the job failed / 任务失败的详细错误信息 */
  error?: string
  /** Processing statistics / 处理统计信息 */
  stats?: {
    /** Number of text chunks created / 创建的文本块数量 */
    chunks: number
    /** Number of RDF triplets (subject-predicate-object) extracted / 提取的三元组数量 */
    triplets: number
    /** Number of concepts identified / 识别的概念数量 */
    concepts: number
    /** Total text length processed / 处理的文本总长度 */
    textLength?: number
  }
  /** Whether AI-powered segmentation was used / 是否使用了 AI 分段 */
  ai_mode?: boolean
  /** AI processing statistics / AI 处理统计信息 */
  ai_stats?: {
    /** Total tokens consumed / 消耗的总 token 数 */
    total_tokens?: number
    /** Prompt (input) tokens / 提示（输入）token 数 */
    prompt_tokens?: number
    /** Completion (output) tokens / 补全（输出）token 数 */
    completion_tokens?: number
    /** Model used (e.g., gpt-4o, claude-3-sonnet) / 使用的模型 */
    model?: string
  }
  /** Insightful messages generated during processing / 处理过程中产生的洞察信息 */
  insights?: string[]
}

/**
 * Descriptor for an available AI provider (e.g., OpenAI, Ollama).
 * AI 提供商的描述信息。
 */
export interface AIProvider {
  /** Unique provider identifier / 提供商标识 */
  id: string
  /** Human-readable display name / 可读的显示名称 */
  name: string
  /** Default model name for this provider / 该提供商的默认模型 */
  default_model: string
  /** Whether an API key is required to use this provider / 是否需要 API key */
  requires_api_key: boolean
}

/**
 * AI-related settings subset, used for configuring AI providers.
 * AI 配置子集，用于配置 AI 服务提供商。
 */
export interface AISettings {
  /** Selected AI provider ID (e.g., "openai", "ollama") / 选中的 AI 提供商 ID */
  ai_provider: string
  /** API key for the selected provider / API 密钥 */
  ai_api_key?: string
  /** Model name override / 模型名称覆写 */
  ai_model?: string
  /** Custom base URL for the provider API / 自定义 API 基础地址 */
  ai_base_url?: string
  /** @deprecated Legacy OpenAI API key (backward compatibility) / 旧版 OpenAI API 密钥（向后兼容） */
  openai_api_key?: string
  /** @deprecated Legacy OpenAI model name / 旧版 OpenAI 模型名称 */
  openai_model?: string
  /** @deprecated Legacy Ollama base URL / 旧版 Ollama 基础地址 */
  ollama_base_url?: string
  /** @deprecated Legacy Ollama model name / 旧版 Ollama 模型名称 */
  ollama_model?: string
}

/**
 * Full system settings, extending AI settings with infrastructure configuration.
 * 完整系统配置，包含 AI 设置与基础设施配置。
 */
export interface Settings extends AISettings {
  /** Neo4j database URI / Neo4j 数据库连接地址 */
  neo4j_uri: string
  /** Neo4j authentication username / Neo4j 认证用户名 */
  neo4j_user: string
  /** Redis connection URL / Redis 连接地址 */
  redis_url: string
  /** Additional dynamic settings / 其他动态设置 */
  [key: string]: any
}

// ===========================================================================
// Dashboard / 仪表盘
// ===========================================================================

/**
 * Fetch aggregate dashboard statistics.
 *
 * GET /graph/stats
 *
 * Returns the total node/edge counts and a breakdown by label and type,
 * used to render summary cards and charts on the dashboard page.
 *
 * @returns A promise resolving to dashboard statistics
 *
 * 获取仪表盘聚合统计信息，包括节点/边总数及其按标签/类型的分布。
 */
export const getDashboardStats = (): Promise<DashboardStats> =>
  api.get('/graph/stats')

// ===========================================================================
// Upload / 上传与导入
// ===========================================================================

/**
 * Extra options accepted by all upload variants.
 * 所有上传接口通用的可选参数。
 */
interface UploadOptions {
  /** Enable AI-powered semantic segmentation / 启用 AI 语义分段 */
  enableAI?: boolean
  /** Custom user prompt for AI segmentation guidance / AI 分段的自定义提示词 */
  userPrompt?: string
  /** Whether to let the backend optimize the user prompt / 是否让后端优化用户提示词 */
  optimizePrompt?: boolean
  /** Root topic for scoping the graph extraction / 用于限定图谱提取范围的根主题 */
  rootTopic?: string
}

/**
 * Upload a file (PDF, DOCX, TXT, etc.) for processing.
 *
 * POST /uploads/process (multipart/form-data)
 *
 * The file is sent as multipart form data. When `auto_process` is true,
 * the backend immediately begins chunking and extraction. Optional AI
 * segmentation can be enabled for smarter document parsing.
 *
 * @param file   - The file to upload (File object from an <input> element)
 * @param options - Optional AI and topic configuration
 * @returns A promise resolving with upload details, including documentId and jobId
 *
 * 上传文件（PDF、DOCX、TXT 等）进行处理。
 * 使用 multipart/form-data 格式传输文件，支持 AI 分段和主题限定。
 */
export const uploadFile = (
  file: File,
  options?: UploadOptions
): Promise<UploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('auto_process', 'true')

  if (options?.enableAI) {
    formData.append('enable_ai_segmentation', 'true')
    if (options.userPrompt) {
      formData.append('user_prompt', options.userPrompt)
    }
    if (options.optimizePrompt !== undefined) {
      formData.append('optimize_prompt', options.optimizePrompt.toString())
    }
  }

  if (options?.rootTopic) {
    formData.append('root_topic', options.rootTopic)
  }

  return api.post('/uploads/process', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * Upload plain text content for processing.
 *
 * POST /uploads/text (application/json)
 *
 * Accepts raw text and an optional title. Unlike uploadFile, the payload
 * is sent as JSON. Supports the same AI segmentation options.
 *
 * @param content    - The raw text content to process / 要处理的原始文本内容
 * @param title      - Optional document title / 可选文档标题
 * @param autoProcess - Whether to auto-start processing (default: true) / 是否自动开始处理（默认 true）
 * @param options    - Optional AI and topic configuration
 * @returns A promise resolving with upload details
 *
 * 上传纯文本内容进行处理。与 uploadFile 不同，请求体为 JSON 格式。
 */
export const uploadText = (
  content: string,
  title?: string,
  autoProcess: boolean = true,
  options?: UploadOptions
): Promise<UploadResponse> => {
  const payload: any = {
    content,
    title,
    auto_process: autoProcess
  }

  if (options?.enableAI) {
    payload.enable_ai_segmentation = true
    if (options.userPrompt) {
      payload.user_prompt = options.userPrompt
    }
    if (options.optimizePrompt !== undefined) {
      payload.optimize_prompt = options.optimizePrompt
    }
  }

  if (options?.rootTopic) {
    payload.root_topic = options.rootTopic
  }

  return api.post('/uploads/text', payload)
}

/**
 * Upload content from a URL for processing.
 *
 * POST /uploads/url (application/json)
 *
 * The backend fetches the content at the given URL and processes it.
 * Supports the same options as file and text uploads.
 *
 * @param url         - The URL to fetch content from / 要抓取内容的 URL
 * @param title       - Optional document title / 可选文档标题
 * @param autoProcess - Whether to auto-start processing (default: true) / 是否自动开始处理
 * @param options     - Optional AI and topic configuration
 * @returns A promise resolving with upload details
 *
 * 从 URL 抓取内容进行处理。后端会请求指定 URL 并处理获取的内容。
 */
export const uploadUrl = (
  url: string,
  title?: string,
  autoProcess: boolean = true,
  options?: UploadOptions
): Promise<UploadResponse> => {
  const payload: any = {
    url,
    title,
    auto_process: autoProcess
  }

  if (options?.enableAI) {
    payload.enable_ai_segmentation = true
    if (options.userPrompt) {
      payload.user_prompt = options.userPrompt
    }
    if (options.optimizePrompt !== undefined) {
      payload.optimize_prompt = options.optimizePrompt
    }
  }

  if (options?.rootTopic) {
    payload.root_topic = options.rootTopic
  }

  return api.post('/uploads/url', payload)
}

/**
 * Trigger ingestion (document chunking + graph extraction) for a previously
 * uploaded document.
 *
 * POST /ingest/{documentId}
 *
 * Starts the background pipeline: text chunking → concept extraction →
 * relationship (triplet) extraction. Returns a job ID for status polling.
 *
 * @param documentId - The document to process / 要处理的文档 ID
 * @returns A promise resolving with ingestion job details
 *
 * 对已上传的文档触发导入流程（分块 + 图谱提取）。
 * 启动后台管道：文本分块 → 概念提取 → 关系（三元组）提取。
 */
export const startIngestion = (documentId: string): Promise<IngestionResponse> =>
  api.post(`/ingest/${documentId}`)

// ===========================================================================
// Documents Management / 文档管理
// ===========================================================================

/**
 * Paginated document list returned by the backend.
 * 后端返回的分页文档列表。
 */
export interface DocumentListResponse {
  /** Total number of documents matching the query / 符合条件的文档总数 */
  total: number
  /** Array of document summaries for the current page / 当前页的文档摘要数组 */
  documents: Array<{
    /** Document ID / 文档 ID */
    id: string
    /** Original filename / 原始文件名 */
    filename: string
    /** Document kind (file, text, url) / 文档类型 */
    kind: string
    /** File size in bytes / 文件大小（字节） */
    size: number
    /** ISO-8601 creation timestamp / 创建时间（ISO-8601） */
    created_at: string
    /** ISO-8601 last-updated timestamp / 最后更新时间（ISO-8601） */
    updated_at: string
    /** File checksum / 文件校验和 */
    checksum: string
    /** Number of text chunks generated / 生成的文本块数量 */
    chunk_count: number
    /** Number of concepts extracted / 提取的概念数量 */
    concept_count: number
    /** Number of claims extracted / 提取的声明数量 */
    claim_count: number
    /** Processing status / 处理状态 */
    processing_status: string
  }>
}

/**
 * Detailed document information including statistics and themes.
 * 文档详细信息，包含统计数据和主题摘要。
 */
export interface DocumentDetail {
  /** Document ID / 文档 ID */
  id: string
  /** Original filename / 原始文件名 */
  filename: string
  /** Document kind / 文档类型 */
  kind: string
  /** File size in bytes / 文件大小（字节） */
  size: number
  /** ISO-8601 creation timestamp / 创建时间 */
  created_at: string
  /** ISO-8601 last-updated timestamp / 最后更新时间 */
  updated_at: string
  /** File checksum / 文件校验和 */
  checksum: string
  /** MIME type / MIME 类型 */
  mime: string
  /** Arbitrary metadata key-value pairs / 任意元数据键值对 */
  meta: Record<string, any>
  /** Processing statistics / 处理统计 */
  statistics: {
    /** Number of chunks / 块数 */
    chunk_count: number
    /** Number of concepts / 概念数 */
    concept_count: number
    /** Number of claims / 声明数 */
    claim_count: number
    /** Number of relations / 关系数 */
    relation_count: number
  }
  /** Extracted themes/topics / 提取的主题列表 */
  themes: Array<{
    /** Theme ID / 主题 ID */
    id: string
    /** Theme label / 主题标签 */
    label: string
    /** Hierarchical level / 层级 */
    level: number
    /** Number of members (documents/concepts) belonging to this theme / 成员数量 */
    member_count: number
    /** Theme summary / 主题摘要 */
    summary: string
  }>
  /** Current processing status / 当前处理状态 */
  processing_status: string
}

/**
 * List all uploaded documents with pagination and sorting.
 *
 * GET /uploads
 *
 * @param skip   - Number of records to skip (for pagination) / 跳过的记录数（分页用）
 * @param limit  - Maximum records to return (page size) / 每页最大记录数
 * @param sortBy - Sort field (default: "created_at") / 排序字段（默认创建时间）
 * @returns A paginated list of document summaries
 *
 * 获取已上传文档的分页列表，支持排序。
 */
export const listDocuments = (skip: number = 0, limit: number = 50, sortBy: string = 'created_at'): Promise<DocumentListResponse> =>
  api.get('/uploads', {
    params: {
      skip,
      limit,
      sort_by: sortBy
    }
  })

/**
 * Get detailed information for a single document.
 *
 * GET /uploads/{documentId}
 *
 * Returns full document metadata, processing statistics, and extracted themes.
 *
 * @param documentId - The document to fetch / 要获取详情的文档 ID
 * @returns Detailed document information
 *
 * 获取单个文档的详细信息，包含元数据、处理统计和提取的主题。
 */
export const getDocumentDetail = (documentId: string): Promise<DocumentDetail> =>
  api.get(`/uploads/${documentId}`)

/**
 * Construct the URL for downloading / previewing a document's raw file.
 *
 * GET /uploads/{documentId}/file
 *
 * This is a URL constructor (not an API call) so the caller can embed the
 * result directly in an <a> or <iframe> element.
 *
 * @param documentId - The document whose file to access / 文档 ID
 * @returns An absolute URL pointing to the raw file endpoint
 *
 * 构造文档原始文件的下载/预览 URL（非 API 调用），可直接用于 <a> 或 <iframe>。
 */
export const getDocumentFileUrl = (documentId: string): string =>
  `${API_BASE}/uploads/${documentId}/file`

/**
 * Delete a document and its associated graph data.
 *
 * DELETE /uploads/{documentId}
 *
 * Cascading deletion: removes the document record, its file (if applicable),
 * all graph edges referencing this document, and orphaned nodes (nodes that
 * become disconnected after edge removal).
 *
 * @param documentId - The document to delete / 要删除的文档 ID
 * @returns Deletion summary statistics
 *
 * 删除文档及其关联的图谱数据。级联删除：文档记录、文件、
 * 所有关联的边以及删除边后成为孤岛的节点。
 */
export const deleteDocument = (documentId: string): Promise<{
  success: boolean
  document_id: string
  filename: string
  file_deleted: boolean
  edges_deleted: number
  orphan_nodes_deleted: number
}> =>
  api.delete(`/uploads/${documentId}`)

// ===========================================================================
// Graph / 图谱数据
// ===========================================================================

/**
 * Retrieve graph data for the visualization canvas.
 *
 * GET /graph/visualize
 *
 * Returns a subset of the full knowledge graph, bounded by a configurable
 * limit (capped at 5000 to prevent frontend overload). Optionally filters
 * by node label.
 *
 * @param limit    - Maximum number of elements to return (clamped to [1, 5000]) / 最大返回数量
 * @returns Graph data payload (structure matches frontend visualization format)
 *
 * 获取知识图谱数据用于前端可视化展示，支持数量限制和节点类型过滤。
 * 最大限制 5000 以防止前端过载。
 */
export const getGraphData = (limit: number = 500): Promise<any> =>
  api.get('/graph/visualize', {
    params: {
      limit: Math.min(limit, 5000)
    }
  })

/**
 * Retrieve graph data filtered by a specific node label.
 *
 * GET /graph/visualize?node_type={nodeType}
 *
 * @param nodeType - Label to filter by (e.g., "Person", "Organization") / 节点标签过滤
 * @param limit    - Maximum elements to return (clamped to [1, 5000]) / 最大返回数量
 * @returns Filtered graph data
 *
 * 按节点标签获取知识图谱数据，用于按类型筛选可视化内容。
 */
export const getGraphDataByType = (nodeType: string, limit: number = 500): Promise<any> =>
  api.get('/graph/visualize', {
    params: {
      limit: Math.min(limit, 5000),
      node_type: nodeType
    }
  })

/**
 * Retrieve the subgraph surrounding a specific document.
 *
 * GET /graph/documents/{documentId}/graph
 *
 * Returns nodes and edges within `depth` hops of the document's associated
 * entities. Depth is clamped to [1, 5] to keep the response manageable.
 *
 * @param documentId - The document to center the subgraph on / 子图中心的文档 ID
 * @param depth      - Traversal depth (1-5, default: 2) / 遍历深度
 * @returns Subgraph data centered on the document
 *
 * 获取以指定文档为中心的局部子图，支持配置遍历深度（1-5）。
 */
export const getDocumentGraph = (documentId: string, depth: number = 2): Promise<any> =>
  api.get(`/graph/documents/${documentId}/graph`, {
    params: {
      depth: Math.max(1, Math.min(depth, 5))
    }
  })

// ===========================================================================
// Query / 查询
// ===========================================================================

/**
 * Execute an arbitrary Cypher query against the Neo4j database.
 *
 * GET /graph/query?cypher={cypher}
 *
 * **Caution**: This endpoint accepts raw Cypher. Ensure proper access controls
 * are in place to prevent Cypher injection in production environments.
 *
 * @param cypher - The Cypher query string to execute / 要执行的 Cypher 查询语句
 * @returns Raw query results (structure depends on the query)
 *
 * 对 Neo4j 数据库执行任意 Cypher 查询。
 * 注意：生产环境中需确保有适当的访问控制以防止 Cypher 注入。
 */
export const executeCypherQuery = (cypher: string): Promise<any> =>
  api.get('/graph/query', { params: { cypher } })

/**
 * Query graph nodes, optionally filtered by label.
 *
 * GET /graph/nodes
 *
 * @param label - Optional node label filter (returns all labels if null) / 节点标签过滤（null 返回全部）
 * @param limit - Maximum nodes to return (default: 100) / 最大返回数量
 * @returns Array of matching nodes
 *
 * 查询图谱节点，可按标签过滤。
 */
export const getNodes = (label: string | null = null, limit: number = 100): Promise<GraphNode[]> => {
  const params: Record<string, any> = { limit }
  if (label) {
    params.label = label
  }
  return api.get('/graph/nodes', { params })
}

/**
 * Query graph edges (relationships), optionally filtered by type.
 *
 * GET /graph/edges
 *
 * @param relType - Optional relationship type filter (returns all types if null) / 关系类型过滤（null 返回全部）
 * @param limit   - Maximum edges to return (default: 100) / 最大返回数量
 * @returns Array of matching edges
 *
 * 查询图谱边（关系），可按关系类型过滤。
 */
export const getEdges = (relType: string | null = null, limit: number = 100): Promise<GraphEdge[]> => {
  const params: Record<string, any> = { limit }
  if (relType) {
    params.rel_type = relType
  }
  return api.get('/graph/edges', { params })
}

// ===========================================================================
// Job Status / 任务状态
// ===========================================================================

/**
 * Poll the status of an ingestion/processing job.
 *
 * GET /uploads/status/{jobId}
 *
 * Used by the frontend to display real-time progress bars and logs
 * during document processing. Returns chunk/triplet/concept counts
 * and AI statistics when applicable.
 *
 * @param jobId - The job to poll / 要轮询的任务 ID
 * @returns Current job status with progress and statistics
 *
 * 轮询导入/处理任务的状态。前端用于在文档处理过程中显示实时进度条和日志。
 */
export const getJobStatus = (jobId: string): Promise<JobStatus> =>
  api.get(`/uploads/status/${jobId}`)

// ===========================================================================
// Settings / 系统设置
// ===========================================================================

/**
 * List all available AI providers.
 *
 * GET /settings/ai-providers
 *
 * Returns providers like OpenAI, Ollama, Claude, etc., along with their
 * default models and whether they require an API key.
 *
 * @returns A list of available AI providers
 *
 * 获取所有可用的 AI 提供商列表，包含默认模型和是否需要 API 密钥的信息。
 */
export const getAIProviders = (): Promise<{ providers: AIProvider[] }> =>
  api.get('/settings/ai-providers')

/**
 * Get the full current system settings.
 *
 * GET /settings/
 *
 * Returns all configuration values including Neo4j connection, Redis URL,
 * and AI provider settings.
 *
 * @returns The complete settings object
 *
 * 获取完整的系统配置，包括 Neo4j 连接信息、Redis URL 和 AI 提供商设置。
 */
export const getSettings = (): Promise<Settings> =>
  api.get('/settings/')

/**
 * Update AI provider settings.
 *
 * POST /settings/ai
 *
 * Persists the selected AI provider, API key, model, and base URL to
 * the backend configuration store.
 *
 * @param settings - The AI settings to save / 要保存的 AI 配置
 * @returns Confirmation response from the backend
 *
 * 更新 AI 提供商设置，持久化到后端配置存储。
 */
export const updateAISettings = (settings: AISettings): Promise<any> =>
  api.post('/settings/ai', settings)

/**
 * Test the connection to a configured AI provider.
 *
 * POST /settings/test-connection
 *
 * Sends a lightweight request to the provider's API to verify that the
 * endpoint, API key, and model name are valid.
 *
 * @param settings - The AI settings to test / 要测试的 AI 配置
 * @returns Connection test result
 *
 * 测试与 AI 提供商的连接，验证端点、API 密钥和模型名称是否有效。
 */
export const testAIConnection = (settings: AISettings): Promise<any> =>
  api.post('/settings/test-connection', settings)

/**
 * Check the health of the Redis connection.
 *
 * GET /settings/redis/health
 *
 * Used by the settings page to verify Redis is reachable and operational.
 *
 * @returns Health check result with Redis status details
 *
 * 检查 Redis 连接的健康状态。
 */
export const getRedisHealth = (): Promise<{ success: boolean; data: any; message: string }> =>
  api.get('/settings/redis/health')

/**
 * List models available from a local Ollama instance.
 *
 * GET /settings/ollama/models
 *
 * Calls the Ollama API's list endpoint through the backend proxy to
 * discover installed and running models.
 *
 * @returns List of available Ollama model names
 *
 * 获取本地 Ollama 实例中可用的模型列表。
 */
export const getOllamaModels = (): Promise<{ success: boolean; models: string[]; message?: string }> =>
  api.get('/settings/ollama/models')

// ===========================================================================
// Graph CRUD Operations / 图谱增删改查
// ===========================================================================

// ---------------------------------------------------------------------------
// Node CRUD / 节点操作
// ---------------------------------------------------------------------------

/**
 * Payload for creating a new graph node.
 * 创建新图谱节点的请求参数。
 */
export interface NodeCreate {
  /** Node labels (e.g., ["Person", "Author"]) / 节点标签列表 */
  labels: string[]
  /** Key-value properties for the node / 节点的键值属性 */
  properties: Record<string, any>
}

/**
 * Payload for updating an existing graph node.
 * 更新已有图谱节点的请求参数。
 */
export interface NodeUpdate {
  /** Updated labels (replaces existing labels) / 更新后的标签列表（完全替换） */
  labels?: string[]
  /** Properties to set or update / 要设置或更新的属性 */
  properties: Record<string, any>
  /** Property keys to remove / 要移除的属性键名列表 */
  remove_properties?: string[]
}

/**
 * Create a new node in the knowledge graph.
 *
 * POST /graph/nodes
 *
 * @param data - Node creation payload (labels + properties) / 节点创建参数
 * @returns The newly created node
 *
 * 在知识图谱中创建一个新节点。
 */
export const createNode = (data: NodeCreate): Promise<GraphNode> =>
  api.post('/graph/nodes', data)

/**
 * Get a single node by its ID.
 *
 * GET /graph/nodes/{nodeId}
 *
 * @param nodeId - The unique node identifier / 节点唯一标识
 * @returns The matching node
 *
 * 根据 ID 获取单个节点。
 */
export const getNode = (nodeId: string): Promise<GraphNode> =>
  api.get(`/graph/nodes/${nodeId}`)

/**
 * Update an existing node.
 *
 * PUT /graph/nodes/{nodeId}
 *
 * Supports updating labels, setting/updating properties, and removing
 * specific properties.
 *
 * @param nodeId - The node to update / 要更新的节点 ID
 * @param data   - Update payload / 更新参数
 * @returns The updated node
 *
 * 更新已有节点的标签和属性。
 */
export const updateNode = (nodeId: string, data: NodeUpdate): Promise<GraphNode> =>
  api.put(`/graph/nodes/${nodeId}`, data)

/**
 * Delete a node from the knowledge graph.
 *
 * DELETE /graph/nodes/{nodeId}?force={force}
 *
 * When `force` is false (default), deletion fails if the node still has
 * relationships. When `force` is true, all connected edges are deleted first.
 *
 * @param nodeId - The node to delete / 要删除的节点 ID
 * @param force  - Whether to force deletion (removes edges first) / 是否强制删除（先删除关联边）
 * @returns Void on success
 *
 * 从知识图谱中删除节点。非强制模式下，如果节点仍有关系则删除失败。
 */
export const deleteNode = (nodeId: string, force: boolean = false): Promise<void> =>
  api.delete(`/graph/nodes/${nodeId}`, { params: { force } })

// ---------------------------------------------------------------------------
// Edge CRUD / 边（关系）操作
// ---------------------------------------------------------------------------

/**
 * Payload for creating a new relationship between two nodes.
 * 创建两个节点间新关系的请求参数。
 */
export interface EdgeCreate {
  /** Source node ID / 起始节点 ID */
  source: string
  /** Target node ID / 目标节点 ID */
  target: string
  /** Relationship type (e.g., "WORKS_AT", "KNOWS") / 关系类型 */
  type: string
  /** Optional key-value properties for the edge / 可选的边属性 */
  properties?: Record<string, any>
}

/**
 * Payload for updating an existing relationship.
 * 更新已有关系的请求参数。
 */
export interface EdgeUpdate {
  /** Updated relationship type / 更新后的关系类型 */
  type?: string
  /** Properties to set or update / 要设置或更新的属性 */
  properties?: Record<string, any>
  /** Property keys to remove / 要移除的属性键名列表 */
  remove_properties?: string[]
}

/**
 * Create a new relationship (edge) between two nodes.
 *
 * POST /graph/edges
 *
 * @param data - Edge creation payload / 边的创建参数
 * @returns The newly created edge
 *
 * 在两个节点之间创建一条新关系。
 */
export const createEdge = (data: EdgeCreate): Promise<GraphEdge> =>
  api.post('/graph/edges', data)

/**
 * Update an existing relationship.
 *
 * PUT /graph/edges/{sourceId}/{targetId}/{relType}
 *
 * The triplet (source, target, type) uniquely identifies the relationship.
 *
 * @param sourceId - Source node ID / 起始节点 ID
 * @param targetId - Target node ID / 目标节点 ID
 * @param relType  - Current relationship type / 当前关系类型
 * @param data     - Update payload / 更新参数
 * @returns The updated edge
 *
 * 更新一条已有关系。三元组（起始节点、目标节点、关系类型）唯一标识一条关系。
 */
export const updateEdge = (sourceId: string, targetId: string, relType: string, data: EdgeUpdate): Promise<GraphEdge> =>
  api.put(`/graph/edges/${sourceId}/${targetId}/${relType}`, data)

/**
 * Delete a relationship.
 *
 * DELETE /graph/edges/{sourceId}/{targetId}/{relType}
 *
 * @param sourceId - Source node ID / 起始节点 ID
 * @param targetId - Target node ID / 目标节点 ID
 * @param relType  - Relationship type / 关系类型
 * @returns Void on success
 *
 * 删除一条关系。通过三元组（起始节点、目标节点、关系类型）定位要删除的关系。
 */
export const deleteEdge = (sourceId: string, targetId: string, relType: string): Promise<void> =>
  api.delete(`/graph/edges/${sourceId}/${targetId}/${relType}`)

// ===========================================================================
// Q&A Service / 问答服务
// ===========================================================================

/**
 * A single chat message in the conversation.
 * 对话中的单条消息。
 */
export interface Message {
  /** Message sender role / 消息发送者角色 */
  role: 'user' | 'assistant'
  /** Message content / 消息正文 */
  content: string
}

/**
 * Request payload for asking a question against the knowledge graph.
 * 向知识图谱提问的请求参数。
 */
export interface AskRequest {
  /** The user's question / 用户的问题 */
  question: string
  /** Optional conversation history for multi-turn context / 可选的多轮对话历史 */
  conversation_history?: Message[]
  /** Whether to ground the answer using the knowledge graph / 是否使用知识图谱来支撑答案 */
  use_kg?: boolean
}

/**
 * Response from the Q&A service.
 * 问答服务的响应结构。
 */
export interface AskResponse {
  /** Whether the request succeeded / 请求是否成功 */
  success: boolean
  /** The generated answer text / 生成的答案文本 */
  answer: string
  /** Whether knowledge graph context was used / 是否使用了知识图谱上下文 */
  used_context: boolean
  /** Snippet of the context used for grounding / 用于支撑答案的上下文片段 */
  context_snippet?: string
  /** Error description if the request failed / 请求失败时的错误描述 */
  error?: string
}

/**
 * Ask a question and receive an answer grounded in the knowledge graph.
 *
 * POST /qa/ask
 *
 * Sends the user's question (with optional conversation history) to the
 * configured AI provider. The answer can optionally be augmented with
 * context retrieved from the knowledge graph (Retrieval-Augmented
 * Generation / RAG).
 *
 * @param request - The question and optional context / 问题及可选上下文
 * @returns The generated answer with context metadata
 *
 * 向知识图谱提问并获取基于图谱的答案。
 * 支持多轮对话历史和基于知识图谱的检索增强生成（RAG）。
 */
export const askQuestion = (request: AskRequest): Promise<AskResponse> =>
  api.post('/qa/ask', request)

/**
 * Check the health and readiness of the Q&A service.
 *
 * GET /qa/health
 *
 * Returns the active AI provider, its connection status, and whether the
 * AI client has been initialized successfully.
 *
 * @returns Health status of the Q&A service
 *
 * 检查问答服务的健康状态，包括 AI 提供商连接状态和客户端初始化情况。
 */
export const checkQAHealth = (): Promise<{ status: string; provider: string; has_ai_client: boolean }> =>
  api.get('/qa/health')
