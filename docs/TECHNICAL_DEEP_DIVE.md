# GraphForge 技术深度解析文档

> **面向人群**: 需要深入理解项目架构的开发者、准备面试的候选人、技术评审者
>
> **前置阅读**: [README.md](../README.md) — 项目简介 | [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) — 文档导航

---

## 目录

- [一、项目概述与系统架构](#一项目概述与系统架构)
  - [1.1 项目定位](#11-项目定位)
  - [1.2 系统架构全景图](#12-系统架构全景图)
  - [1.3 核心事务流程](#13-核心事务流程)
- [二、模块深度剖析](#二模块深度剖析)
  - [2.1 基础设施层 (Infrastructure)](#21-基础设施层-infrastructure)
  - [2.2 数据模型层 (Models)](#22-数据模型层-models)
  - [2.3 业务服务层 (Services)](#23-业务服务层-services)
  - [2.4 API 路由层 (Routes)](#24-api-路由层-routes)
  - [2.5 GraphRAG 九阶段流水线](#25-graphrag-九阶段流水线)
  - [2.6 前端应用层](#26-前端应用层)
  - [2.7 模块联动关系矩阵](#27-模块联动关系矩阵)
- [三、技术栈深度对比与选型理由](#三技术栈深度对比与选型理由)
- [四、面试问答](#四面试问答)

---

## 一、项目概述与系统架构

### 1.1 项目定位

GraphForge 是一个**面向软件工程领域的多模态知识图谱增量式构建平台**。它的核心目标是将非结构化文档（PDF、Markdown、TXT、Word）自动转化为结构化的知识图谱，并通过交互式可视化、智能问答和知识卡片提供知识检索能力。

**核心竞争壁垒**：
1. **GraphRAG 流水线**：实现了从"文档 → Chunk → Entity → Claim → Theme → Neo4j"的九阶段全自动管道
2. **多AI提供商统一接口**：通过工厂模式 + OpenAI兼容协议，支持12种AI提供商的热切换
3. **领域强约束**：通过本体定义（Ontology）、谓词白名单（Predicate Allowlist）、领域过滤器（Domain Filter）、类型约束（Type Constraints）四层过滤机制，确保生成的知识图谱高度聚焦软件工程领域
4. **增量构建能力**：基于 Neo4j MERGE 幂等写入和内容快照对比，仅处理新增/变更内容

### 1.2 系统架构全景图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Frontend Layer (Browser)                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Dashboard │ │  Upload  │ │  Graph   │ │  Query   │ │  Settings        │ │
│  │ (统计数据) │ │ (文档上传) │ │ (图谱可视化)│ │ (智能问答) │ │  (AI配置/数据库) │ │
│  └─────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘ │
│        │             │            │             │               │            │
│  ┌─────┴─────────────┴────────────┴─────────────┴───────────────┴─────────┐ │
│  │                         API Layer (api/index.ts)                        │ │
│  │    Axios Instance → Request Interceptor → Response Interceptor          │ │
│  │    Base URL: VITE_API_BASE || http://localhost:8000                     │ │
│  └──────────────────────────────────┬──────────────────────────────────────┘ │
│  ┌─────┴─────────────┐ ┌───────────┴───────────┐ ┌────────────────────────┐ │
│  │  Pinia Stores     │ │ Vue Router (8 routes) │ │ Components (5 reusable) │ │
│  │  app.ts / proc.ts │ │ History Mode          │ │ CommandPalette etc.     │ │
│  └───────────────────┘ └───────────────────────┘ └────────────────────────┘ │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │ HTTP/WebSocket
┌──────────────────────────────────┴──────────────────────────────────────────┐
│                          API Layer (FastAPI)                                  │
│  ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌────────────────┐  │
│  │ /uploads  │ │ /ingest  │ │ /graph   │ │ /qa       │ │ /settings      │  │
│  │ /knowledge│ │  (6 routes)│ │  (upload)│ │  (ingest) │ │  (qa)          │  │
│  │ -cards    │ │           │ │          │ │           │ │                │  │
│  └─────┬─────┘ └─────┬────┘ └────┬─────┘ └─────┬─────┘ └───────┬────────┘  │
└────────┼─────────────┼───────────┼─────────────┼───────────────┼───────────┘
         │             │           │             │               │
┌────────┴─────────────┴───────────┴─────────────┴───────────────┴───────────┐
│                       Service Layer (Business Logic)                         │
│  ┌───────────┐ ┌─────────────┐ ┌──────────────┐ ┌───────────┐              │
│  │ Parser    │ │ AISegmenter  │ │ Extractor    │ │ Linker    │              │
│  │ (工厂模式) │ │ (语义分块)   │ │ (三元组提取)  │ │ (实体消歧) │              │
│  └─────┬─────┘ └──────┬──────┘ └──────┬───────┘ └─────┬─────┘              │
│        │              │              │               │                       │
│  ┌─────┴──────────────┴──────────────┴───────────────┴───────────────────┐ │
│  │              GraphRAG Pipeline (9 Stages)                              │ │
│  │  Stage0 → Stage1 → Stage2 → Stage3 → Stage4 → Stage5 → Stage6 → S7→S8 │ │
│  │  Chunker  Coref   Linker  Extract  Theme   Pred.   Graph   Query/Metr  │ │
│  └───────────────────────────────────┬────────────────────────────────────┘ │
│                                      │                                       │
│  ┌───────────────────────────────────┴────────────────────────────────────┐ │
│  │                     Infrastructure Layer                                │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │ │
│  │  │ Neo4j Client │  │ AI Providers │  │ Redis Queue  │                 │ │
│  │  │ (图数据库)    │  │ (12 Providers)│  │ (RQ + Redis) │                 │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                 │ │
│  └─────────┼─────────────────┼─────────────────┼──────────────────────────┘ │
└────────────┼─────────────────┼─────────────────┼────────────────────────────┘
             │                 │                 │
    ┌────────┴────┐   ┌───────┴───────┐  ┌──────┴───────┐
    │    Neo4j    │   │ OpenAI/Claude │  │    Redis     │
    │  (图数据库)  │   │  DeepSeek...  │  │  (队列+缓存)  │
    └─────────────┘   └───────────────┘  └──────────────┘
```

### 1.3 核心事务流程

#### 事务一：文档上传与知识抽取（异步流程）

```
用户拖拽文件               前端 Upload.vue              后端 upload.py
    │                         │                          │
    ├─1.选择文件──────────────→│                          │
    │                         ├─2. POST /uploads─────────→│
    │                         │  (FormData + file)       ├─3. storage.py 存储文件
    │                         │                          ├─4. neo4j_client 创建 Document 节点
    │                         │                          ├─5. 返回 document_id
    │                         │←─────────────────────────┤
    │                         │                          │
    │                         ├─6. POST /ingest──────────→│
    │                         │  ({"document_id": X})    ├─7. queue.py 入队异步任务
    │                         │                          │  ┌──────────────────────┐
    │                         │                          │  │ Worker 异步执行:      │
    │                         │                          │  │  ├ parser.py  解析文档│
    │                         │                          │  │  ├ ai_segmenter 语义分块│
    │                         │                          │  │  ├ extractor 三元组提取│
    │                         │                          │  │  ├ linker 实体链接合并│
    │                         │                          │  │  └ neo4j_client 图谱落库│
    │                         │                          │  └──────────────────────┘
    │                         │                          │
    │                         ├─8. polling: GET /ingest/status──→│
    │  ← 进度条更新            │←──{status, progress}────┤
    │                         │                          │
```

**关键联动点**：
- `ProcessingFloater.vue` 通过 `stores/processing.ts` 的轮询机制每2秒查询任务状态
- `queue.py` 使用 RQ (Redis Queue) 支持任务取消（cancel_job 通过 Redis 信号 + 检查 SIGTERM 取消令牌）
- `config_service.py` 将 AI 配置持久化到 Neo4j 的 `SystemConfig` 节点，确保 Worker 进程读取最新配置

#### 事务二：GraphRAG 九阶段流水线（知识图谱构建核心）

```
输入: 文档文本 (parser 输出)
  │
  ├─ Stage 0: Chunker (篇章切分)
  │  └─ 滑动窗口切分，窗口大小 4 句，步长 2 句
  │
  ├─ Stage 1: Coref (指代消解)
  │  └─ 代词映射、括号别名识别、候选评分
  │
  ├─ Stage 2: Entity Linker (实体链接)  ←── 第一道领域过滤
  │  ├─ BM25 + 向量混合检索候选实体
  │  ├─ 精排打分 (词形 0.2 + 语义 0.4 + 上下文 0.2 + 类型 0.1 + 先验 0.1)
  │  ├─ domain_filter.is_software_engineering_entity() 领域过滤
  │  └─ 自动接受(>0.85) / 待复核(0.65-0.85) / 拒绝(<0.65)
  │
  ├─ Stage 3: Claim Extractor (论断抽取)
  │  ├─ LLM 提取结构化三元组 (主体-谓词-客体)
  │  ├─ 提示词限定软件工程领域 (claim_extraction.txt)
  │  └─ 置信度过滤 (min_confidence: 0.7)
  │
  ├─ Stage 4: Theme Builder (主题构建)
  │  ├─ Louvain 社区检测 (多尺度: resolution 0.5/1.5)
  │  └─ LLM 主题摘要生成
  │
  ├─ Stage 5: Predicate Governor (谓词治理)  ←── 第二道关系过滤
  │  ├─ 自然语言谓词 → 标准谓词映射 (如 "属于" → BELONGS_TO)
  │  ├─ unmapped 谓词 → 直接拒绝 (mode: reject)
  │  └─ 类型约束检查 (头类型, 谓词, 尾类型) 白名单
  │
  ├─ Stage 6: Graph Service (图谱存储)  ←── 第三道类型过滤
  │  ├─ ALLOWED_ENTITY_TYPES 白名单 (5种实体)
  │  ├─ ALLOWED_RELATIONSHIP_TYPES 白名单 (5种关系)
  │  └─ Neo4j MERGE 幂等写入
  │
  ├─ Stage 7: Query Service (查询服务)
  │  ├─ Local Search: 图遍历 (max 2 hops, 50 nodes)
  │  ├─ Global Search: Top-K 社区检索
  │  └─ Hybrid Search: local 0.6 + global 0.4
  │
  └─ Stage 8: Metrics Service (度量服务)
     ├─ 覆盖率 / 准确率 / 一致性 / 连接性 评估
     └─ 孤立节点告警 (阈值 5%)
```

**关键联动点**：
- 每个 Stage 通过明确的输入/输出数据模型（Chunk, Claim, Theme, Feedback）串联
- 配置统一从 `config/*.yaml` 加载，覆盖 `env` 变量
- 领域过滤器贯穿 Stage 2/5/6 三重过滤，确保图谱质量

#### 事务三：智能问答（上下文增强检索）

```
用户提问                    前端 Query.vue            后端 qa.py
  │                             │                       │
  ├─1.输入问题──────────────────→│                       │
  │                             ├─2. POST /qa/ask───────→│
  │                             │                       ├─3. qa_service.answer_question()
  │                             │                       │   ├─ _extract_keywords()
  │                             │                       │   ├─ query_knowledge_graph()
  │                             │                       │   │  └─ Cypher MATCH (n:Concept)
  │                             │                       │   │     WHERE name/alias CONTAINS keyword
  │                             │                       │   │     OPTIONAL MATCH (n)-[r]-(related)
  │                             │                       │   ├─ _format_context()
  │                             │                       │   │  └─ 格式化为 JSON 文本
  │                             │                       │   ├─ AI chat_completion()
  │                             │                       │   │  System: "You are an expert..."
  │                             │                       │   │  User: context + question
  │                             │                       │   └─ 返回答案
  │                             │←──{answer, references}─┤
  │                             │                       │
  │  ← Markdown 渲染 + 引用标注  │                       │
```

**关键联动点**：
- QA 服务直接依赖 `neo4j_client`（查询实体）和 `ai_providers`（LLM 生成答案）
- 上下文窗口限制 2000 字符，超限截断最近关系
- 前端 `QADialog.vue` 支持 Markdown 渲染和上下文引用折叠面板

---

## 二、模块深度剖析

### 2.1 基础设施层 (Infrastructure)

#### 2.1.1 Neo4jClient — 图数据库客户端 (`neo4j_client.py`, ~1039行)

**核心职责**：
- 连接管理（30次重试，认证/连接错误区分处理）
- Schema 初始化（约束 + 索引自动创建）
- 类型转换（Neo4j DateTime → Python str，嵌套对象 → 基元类型）
- 完整 CRUD（Document, Concept, Topic, Relationship）
- 双语概念搜索（中英文 + 别名匹配）
- 级联删除（递归孤儿节点清理）

**设计亮点**：

1. **连接重试策略**：区分认证错误（即时失败）与连接错误（可重试），支持 Docker 环境下 Neo4j 启动延迟场景。最多重试 30 次，间隔 2 秒。

2. **Schema 自动初始化**：首次连接时自动执行 schema.cypher 创建约束和索引，使用 Cypher IF NOT EXISTS 语法保证幂等。

3. **类型安全转换**：`_convert_neo4j_value()` 递归处理 Neo4j 特殊类型（DateTime、Node、Relationship），确保 JSON 序列化兼容。路径示例：
   ```
   DateTime → ISO 8601 字符串
   Node → Dict[id, labels, properties]
   Relationship → Dict[id, type, source, target, properties]
   ```

4. **属性净化**：`_sanitize_properties()` 将嵌套对象拍平为字符串（JSON），确保 Cypher 参数兼容性。

5. **双语搜索**：`find_similar_concepts()` 使用 `apoc.text.clean` + `apoc.text.phonetic` 实现中英文混合模糊搜索。

**面试考察点**：
- 为什么不用 OGM（如 neomodel）而用原生驱动？ → 灵活控制 Cypher 查询，MERGE 幂等写入，批量操作优化
- 连接池如何管理？ → Neo4j Python Driver 内置连接池，`max_connection_lifetime` 和 `max_connection_pool_size` 配置

#### 2.1.2 AIProviderFactory — 多提供商统一接口 (`ai_providers.py`, ~902行)

**核心职责**：
- 12 种 AI 提供商的统一接口（OpenAI, Anthropic, Google Gemini, DeepSeek, Qwen, GLM, Moonshot, Ernie, MiniMax, Doubao, Ollama, Mock）
- 工厂模式创建客户端，运行时热切换
- OpenAI 兼容协议适配层（Google Gemini 等非 OpenAI 原生服务通过此层接入）

**设计亮点**：

1. **工厂模式 + 策略模式**：
   ```
   BaseAIClient (抽象接口)
     ├── OpenAIClient (OpenAI 原生 SDK)
     ├── AnthropicClient (Anthropic 原生 SDK)
     ├── GoogleGeminiClient (OpenAI 兼容包装)
     ├── OpenAICompatibleClient (DeepSeek, Qwen, GLM... 6种国产模型)
     └── MockClient (测试用)
   
   AIProviderFactory.create_client(provider, api_key, model, base_url)
       → 返回对应的客户端实例
   ```

2. **OpenAI 兼容协议适配**：对于不支持原生 OpenAI SDK 的服务（如 Google Gemini），通过自定义 `_GoogleCompatibleOpenAI` 子类覆盖 `_request()` 方法，在发送请求前转换 message 格式并注入 Gemini 特有的 `generationConfig`。

3. **运行时热切换**：AI 配置持久化到 Neo4j `SystemConfig` 节点，`config_service.py` 提供读写接口，前端 `Settings.vue` 支持无重启切换 AI 提供商。

4. **JSON Mode 支持**：通过 `response_format={"type": "json_object"}` + system prompt 强制 JSON 输出，利用正则提取和修复截断的 JSON。

**面试考察点**：
- 工厂模式 vs 依赖注入？ → 此处用工厂模式更合适：运行时根据配置创建不同客户端，调用方无需知道具体类型
- OpenAI 兼容协议的好处？ → 6 种国产模型可复用同一套代码，降低维护成本
- 如何保证 JSON Mode 的可靠性？ → 正则提取 + 截断修复 + 重试机制

#### 2.1.3 RedisQueue — 异步任务队列 (`queue.py`, ~552行)

**核心职责**：
- 基于 RQ (Redis Queue) 的异步任务执行
- 连接池管理 + 自动重试 + 降级策略
- 任务状态追踪（PENDING → STARTED → FINISHED/FAILED）
- 任务取消（通过 Redis 信号 + Worker 检查取消令牌）
- 命名空间隔离的缓存工具函数

**设计亮点**：

1. **优雅降级**：当 Redis 不可用时，返回 `None`；调用方（如 `ingest.py`）使用内存字典作为降级方案。

2. **密码自动注入**：`_build_redis_url()` 自动检测 URL 中是否包含认证信息，若无则注入 `redis_password` 配置。

3. **连接池单例**：进程级单例，`decode_responses=False`（RQ 使用 pickle 序列化需要二进制协议）。

4. **取消机制**：`cancel_job()` 发送 Redis 取消信号 + 调用 `job.cancel()` → Worker 在下次检查取消令牌时终止执行。

**面试考察点**：
- 为什么选 RQ 而不是 Celery？ → 见技术栈对比章节
- 任务取消如何保证可靠性？ → Redis 信号 + Python SIGTERM + Worker 主动检查三重保障
- 连接池为什么要 `decode_responses=False`？ → RQ 使用 pickle 序列化，需要二进制协议

#### 2.1.4 ConfigService — 运行时配置管理 (`config_service.py`, ~239行)

**核心职责**：
- 运行时配置读写（持久化到 Neo4j SystemConfig 节点）
- 环境变量作为默认值，运行时配置优先级更高
- `get_runtime_config()` 返回完整配置字典（含默认值补充）

**设计亮点**：
- 两层配置优先级：`env 变量 (Settings())` < `Neo4j SystemConfig (运行时)`
- API Key 安全：读取时返回 `"***"` 遮蔽，写入时仅当非 `"***"` 才更新

#### 2.1.5 FileStorage — 文件存储 (`storage.py`, ~150行)

**核心职责**：
- 文件上传存储（本地文件系统）
- 文件命名（UUID + 原始扩展名）
- 文件清理（级联删除 + 子目录递归清理）

### 2.2 数据模型层 (Models)

| 模型 | 文件 | 核心字段 | 用途 |
|------|------|---------|------|
| `Document` / `DocumentCreate` | `document.py` | id, title, kind, file_path, content_hash, status, chunks_count, processed_at | 文档实体与上传请求 |
| `Chunk` | `document.py` | doc_id, chunk_id, text, meta, embedding | 文档语义分块 |
| `GraphNode` | `graph.py` | id, labels, properties, created_at, updated_at | 图谱节点 CRUD |
| `GraphEdge` | `graph.py` | id, source, target, type, properties | 图谱关系 CRUD |
| `GraphData` / `GraphQuery` | `graph.py` | nodes[], edges[], total, query_time_ms | 图谱可视化数据 + 查询参数 |
| `GraphStats` | `graph.py` | node_count, edge_count, node_types, relationship_types, density, avg_degree | 图谱统计指标 |
| `KnowledgeCard` | `knowledge_card.py` | id, name, domain, category, description, importance, aliases, related[] | 知识卡片 CRUD |
| `Triplet` | (`extractor.py` 隐式定义) | subject, predicate, object, confidence | 三元组（知识图谱基本单元） |

**设计原则**：
- 所有模型使用 Pydantic v2 进行运行时类型校验
- 请求/响应模型分离（Create/Update/Response 三类）
- 统一响应格式：`{"success": bool, "data": T, "message": str}`

### 2.3 业务服务层 (Services)

#### 服务依赖关系图

```
┌─────────────┐
│   Parser    │ ← 文档解析入口（工厂模式：PDF/DOCX/TXT/MD）
│ (parser.py) │
└──────┬──────┘
       │ full_text + chunks[]
       ▼
┌──────────────┐
│ AISegmenter  │ ← 语义分块与文档结构分析（LLM 辅助）
│(ai_segmenter)│
└──────┬───────┘
       │ 精炼后的 chunks[]
       ▼
┌──────────────┐
│  Extractor   │ ← 三元组提取（LLM 生成结构化论断）
│(extractor.py)│
└──────┬───────┘
       │ Triplet[] claims
       ▼
┌──────────────┐
│   Linker     │ ← 实体消歧与链接合并（BM25 + 向量混合检索）
│ (linker.py)  │
└──────┬───────┘
       │ LinkedEntity[]
       ▼
┌──────────────┐
│GraphService  │ ← Neo4j MERGE 幂等存储
│(graph_serv)  │
└──────┬───────┘
       │ 查询实体+关系
       ▼
┌──────────────┐
│  QAService   │ ← 智能问答（KG 检索 + LLM 生成）
│(qa_service)  │
└──────────────┘
```

#### 2.3.1 Parser — 文档解析 (`parser.py`, ~555行)

**工厂模式实现**：
```python
class ParserFactory:
    _parsers = {
        "pdf": PDFParser,      # PyMuPDF (fitz)
        "txt": TxtParser,      # 原生 open()
        "markdown": MarkdownParser,  # re 正则清理 Markdown 标记
        "docx": WordParser,    # python-docx
    }

    @staticmethod
    def create_parser(kind: str, chunk_size: int = 2000) -> Parser:
        return ParserFactory._parsers[kind](chunk_size=chunk_size)
```

**智能分块算法**：
1. 若文本 ≤ chunk_size → 单块返回
2. 按段落 (`\n\n`) 分割 → 累积段落至接近 chunk_size
3. 超大段落 → 按句子 (`[.!?]`) 分割
4. 超大句子 → 按词分割

#### 2.3.2 Extractor — 三元组提取 (`extractor.py`, ~383行)

调用 AI 将自然语言文本转化为结构化三元组：
```
输入: "工厂模式（Factory Pattern）是 GoF 23 种设计模式之一..."
输出: [
  {subject: "工厂模式", predicate: "BELONGS_TO", object: "设计模式", confidence: 0.95},
  {subject: "工厂模式", predicate: "FROM", object: "GoF 设计模式", confidence: 0.88}
]
```

AI 提示词 (`claim_extraction.txt`) 限定仅提取软件工程领域知识，并指定5种标准谓词。

#### 2.3.3 Linker — 实体链接 (`linker.py`, ~390行)

**混合检索 + 精排**：
1. BM25 词形检索 → Top-20 候选
2. 向量相似度检索 → Top-20 候选（通过 OpenAI text-embedding-3-small, 1536维）
3. 合并去重 → Top-10
4. 精排打分（词形 0.2 + 语义 0.4 + 上下文 0.2 + 类型 0.1 + 先验 0.1）
5. 领域过滤器（`domain_filter.is_software_engineering_entity()`）
6. 自动接受 (>0.85) / 待复核 (0.65-0.85) / 拒绝 (<0.65)

### 2.4 API 路由层 (Routes)

| 路由前缀 | 文件 | 关键端点 | HTTP方法 |
|---------|------|---------|----------|
| `/uploads` | `upload.py` (1368行) | 文件/文本/URL上传，文档列表，文档详情，文档删除 | POST, GET, DELETE |
| `/ingest` | `ingest.py` (692行) | 提交处理任务，任务状态查询，任务取消 | POST, GET, DELETE |
| `/graph` | `graph.py` (1212行) | 图谱数据，文档子图，概念子图，统计信息，节点/边 CRUD | GET, POST, PUT, DELETE |
| `/qa` | `qa.py` (169行) | 问答，历史记录，答案反馈 | POST, GET |
| `/knowledge-cards` | `knowledge_card.py` (579行) | 概念列表，概念详情，概念创建/更新/删除，关系创建 | GET, POST, PUT, DELETE |
| `/settings` | `settings.py` (404行) | AI提供商列表，系统设置读写，连接测试，Redis健康，Ollama模型发现 | GET, POST |

**统一响应格式**：
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 2.5 GraphRAG 九阶段流水线

#### 完整数据流

```
Stage 0: SemanticChunker
  Input:  原始文档文本
  Output: Chunk[] (滑动窗口: window=4句, step=2句)
  Config: thresholds.yaml → chunking
  └─→

Stage 1: CoreferenceResolver  
  Input:  Chunk[]
  Output: Chunk[] (代词被替换为全称，括号别名被识别并注入)
  Config: thresholds.yaml → coreference
  └─→

Stage 2: EntityLinker  ←── 第一道领域过滤
  Input:  Chunk[] + 知识库已有实体 (Neo4j)
  Output: LinkedEntity[] (含 mention → entity 映射)
  Config: ontology.yaml, predicates.yaml, thresholds.yaml
  Tools:  domain_filter.py, embedding.py, nli_verifier.py
  └─→

Stage 3: ClaimExtractor
  Input:  Chunk[] + LinkedEntity[]
  Output: Claim[] (结构化的 (主体, 谓词, 客体, 置信度) 三元组)
  Config: thresholds.yaml → claim_extraction
  Prompt: claim_extraction.txt (领域限定提示词)
  Tools:  text_processing.py
  └─→

Stage 4: ThemeBuilder
  Input:  Claim[] + Entity[]
  Output: Theme[] (含 hierarchy, summary, members[])
  Config: thresholds.yaml → theme_building
  Algo:   Louvain 社区检测 (resolution 0.5/1.5 多尺度)
  └─→

Stage 5: PredicateGovernor  ←── 第二道关系过滤
  Input:  Claim[]
  Output: Claim[] (谓词被规范化为5种标准，非标准谓词被过滤)
  Config: predicates.yaml (白名单 + 映射表)
  Tools:  claim_deduplicator.py, validation.py
  └─→

Stage 6: GraphService  ←── 第三道类型过滤
  Input:  Entity[] + Claim[]
  Output: Neo4j 节点和关系 (MERGE 幂等写入)
  Config: ontology.yaml (ALLOWED_ENTITY_TYPES + ALLOWED_RELATIONSHIP_TYPES)
  └─→

Stage 7: QueryService
  Input:  用户查询 + 图谱 (Neo4j)
  Output: 检索结果 (entities, communities, evidence)
  Config: thresholds.yaml → query
  Modes:  Local Search (图遍历) / Global Search (社区检索) / Hybrid
  └─→

Stage 8: MetricsService
  Input:  图谱元数据
  Output: 质量报告 (覆盖率、准确率、一致性、连接性)
  Config: thresholds.yaml → metrics
```

#### 多层过滤体系图

```
┌──────────────────────────────────────┐
│         Layer 1: Prompt 限定           │
│  claim_extraction.txt 限定领域        │
│  entity_linking.txt 限定实体类型       │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│         Layer 2: Domain Filter       │
│  domain_filter.py                   │
│  - 200+ 软件工程关键词               │
│  - is_software_engineering_entity()  │
│  - is_valid_relationship()          │
│  - confidence_threshold: 0.3        │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│       Layer 3: Predicate Governor     │
│  predicates.yaml                    │
│  - 5 种标准谓词白名单                 │
│  - 自然语言 → 标准谓词映射           │
│  - 未匹配谓词 → reject (直接拒收)    │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│       Layer 4: Ontology Constraint    │
│  ontology.yaml                      │
│  - 5 种实体类型白名单                 │
│  - 5 种关系类型白名单                 │
│  - 类型约束 (source, predicate, target)│
└──────────────────────────────────────┘
```

### 2.6 前端应用层

#### 组件树

```
App.vue (根组件)
  ├── AppContent.vue (Naive UI 引导 + window.$message 暴露)
  │   └── <router-view> ──────────────────────────────────────
  │       ├── Dashboard.vue     (仪表盘 - 统计概览)
  │       ├── Upload.vue        (文档上传 - 三Tab上传)
  │       ├── Documents.vue     (文档管理 - 列表/搜索/删除)
  │       ├── Graph.vue         (图谱可视化 - Cytoscape.js 交互)
  │       ├── Query.vue         (Cypher 查询 + 图查询)
  │       ├── KnowledgeCard.vue (知识卡片 - CRUD)
  │       ├── Status.vue        (任务状态 - 进度跟踪)
  │       └── Settings.vue      (系统设置 - AI/DB 配置)
  │
  ├── MainLayout.vue (布局 - 页头/导航/搜索/主题切换)
  ├── CommandPalette.vue (命令面板 - Ctrl+K)
  ├── ProcessingFloater.vue (处理状态浮窗)
  ├── QADialog.vue (智能问答对话框)
  ├── EmptyState.vue (空状态占位)
  └── stores/
      ├── app.ts (语言/主题 持久化)
      └── processing.ts (任务轮询/进度追踪)
```

#### ProcessingStore 轮询机制

```typescript
// stores/processing.ts 核心逻辑
startPolling(jobId: string) {
  // 1. 立即查询一次状态（避免等待首个 interval）
  this.pollTaskStatus(jobId)

  // 2. 每 2 秒查询一次
  const timer = setInterval(() => {
    const task = this.tasks.get(jobId)
    // 如果任务已终止 (completed/failed/cancelled)，自动停止轮询
    if (task && ['completed', 'failed', 'cancelled'].includes(task.status)) {
      clearInterval(timer)
      return
    }
    this.pollTaskStatus(jobId)
  }, 2000)

  this._pollingTimers.set(jobId, timer)
}
```

#### Cytoscape.js 可视化 (`Graph.vue`)

**支持的布局** (5种):
1. **dagre** — 层次布局（适合树形/层级关系展示）
2. **breadthfirst** — 广度优先布局
3. **concentric** — 同心圆布局（中心节点突出）
4. **cose** — 力导向布局（CoSE 算法, 模拟物理弹簧）
5. **grid** — 网格布局

**交互功能**:
- 节点/边点击高亮 + 邻居节点聚焦
- 右键上下文菜单（编辑/删除节点）
- 全文搜索（模糊匹配，焦点动画跳转）
- 文档过滤（按文档 ID 筛选子图）
- 缩放/导出 (PNG)
- 图例（5种实体类型颜色映射）

### 2.7 模块联动关系矩阵

| 触发事件 | 前端模块 | API路由 | Service | Infra | GraphRAG | 数据存储 |
|---------|---------|---------|---------|-------|----------|---------|
| 文件上传 | Upload.vue → api/services.ts | upload.py (POST /uploads) | — | storage.py (文件存储) | — | Neo4j (Document节点) |
| 知识抽取 | Upload.vue → ProcessingFloater | ingest.py (POST /ingest) | parser → extractor → linker | queue.py (RQ入队) → ai_providers (LLM调用) | Stage 0→6 | Neo4j (实体+关系节点) |
| 进度轮询 | processing.ts (2s interval) | ingest.py (GET /status) | — | queue.py (get_job_status) | — | Redis (RQ Job元数据) |
| 图谱可视化 | Graph.vue (Cytoscape) | graph.py (GET /graph) | graph_service.py | neo4j_client (Cypher) | — | Neo4j (查询) |
| 智能问答 | Query.vue → QADialog | qa.py (POST /qa/ask) | qa_service.py | ai_providers (LLM) + neo4j_client | Stage 7 (查询) | Neo4j (上下文检索) |
| AI配置切换 | Settings.vue | settings.py (POST /settings/ai) | config_service.py | ai_providers (客户端重建) | — | Neo4j (SystemConfig) |
| 知识卡片CRUD | KnowledgeCard.vue | knowledge_card.py | — | neo4j_client | — | Neo4j (KnowledgeCard) |

---

## 三、技术栈深度对比与选型理由

### 3.1 后端框架：FastAPI vs Flask vs Django

| 维度 | FastAPI (本项目选择) | Flask | Django |
|------|---------------------|-------|--------|
| **类型安全** | ✅ Pydantic v2 自动校验 | ❌ 需手动校验 | ⚠️ DRF Serializer |
| **异步支持** | ✅ 原生 async/await | ⚠️ 需扩展 (Quart) | ⚠️ Django 3.1+ 部分支持 |
| **自动文档** | ✅ Swagger + ReDoc 自动生成 | ❌ 需 flasgger 等扩展 | ⚠️ drf-spectacular |
| **性能** | ⭐⭐⭐⭐⭐ (Uvicorn, ~30k req/s) | ⭐⭐⭐ (WSGI) | ⭐⭐⭐ (WSGI) |
| **学习曲线** | ⭐⭐⭐ (中等) | ⭐⭐⭐⭐ (简单) | ⭐⭐ (陡峭) |
| **生态成熟度** | ⭐⭐⭐⭐ (快速增长) | ⭐⭐⭐⭐⭐ (成熟) | ⭐⭐⭐⭐⭐ (成熟) |

**选择理由**：
1. **Pydantic 类型校验**：本项目涉及大量 AI 输出的结构化数据校验（三元组、实体、关系），Pydantic v2 的类型系统极大减少了运行时错误。
2. **原生异步 I/O**：文档解析、AI 调用、Neo4j 查询均为 I/O 密集型操作，async/await 避免了线程池管理的复杂性。
3. **自动 API 文档**：12 种 AI 提供商接口、30+ API 端点，Swagger UI 自动生成让团队和 AI 系统易于对接。

### 3.2 图数据库：Neo4j vs ArangoDB vs JanusGraph

| 维度 | Neo4j (本项目选择) | ArangoDB | JanusGraph |
|------|-------------------|----------|------------|
| **图查询语言** | ✅ Cypher (类 SQL 声明式) | AQL (ArangoDB Query Language) | Gremlin (图遍历) |
| **GraphRAG 集成** | ✅ 原生 neo4j-graphrag 库 | ❌ 自建 | ❌ 自建 |
| **MERGE 幂等** | ✅ Cypher MERGE | ⚠️ UPSERT | ⚠️ 手动处理 |
| **社区/生态** | ⭐⭐⭐⭐⭐ (最成熟图数据库) | ⭐⭐⭐ | ⭐⭐⭐ |
| **可视化** | ✅ Neo4j Browser | ⚠️ ArangoDB Web Interface | ❌ 需第三方 |
| **部署** | ⭐⭐⭐⭐⭐ (Docker, Aura Cloud) | ⭐⭐⭐⭐ | ⭐⭐ (需 Cassandra/HBase) |

**选择理由**：
1. **MERGE 幂等写入**：增量构建的核心需求——同一知识点重复上传时不会创建重复节点，而是更新属性并追加别名。
2. **Cypher 语言**：声明式图查询比 Gremlin 遍历式查询更易读易维护，尤其适合复杂的知识图谱多跳查询。
3. **neo4j-graphrag**：Microsoft GraphRAG 官方推荐的 Neo4j 集成库，支持向量索引、混合搜索、社区检测。
4. **GDS 库**：Louvain 社区检测、PageRank、Betweenness Centrality 等图算法直接可用。

### 3.3 前端框架：Vue 3 vs React vs Angular

| 维度 | Vue 3 (本项目选择) | React 18 | Angular |
|------|-------------------|----------|---------|
| **学习曲线** | ⭐⭐⭐⭐ (渐进式) | ⭐⭐⭐ (JSX需适应) | ⭐⭐ (陡峭) |
| **TypeScript支持** | ⭐⭐⭐⭐⭐ (Composition API 完美支持) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **状态管理** | ✅ Pinia (官方推荐) | ⚠️ Redux/Zustand/Jotai (碎片化) | ✅ RxJS + Signals |
| **构建工具** | ✅ Vite (极速HMR) | ⚠️ CRA/Next.js/Vite | ⭐⭐⭐ (Angular CLI) |
| **UI组件库** | ✅ Naive UI (Vue 3原生) | ✅ Ant Design/shadcn | ✅ Angular Material |
| **响应式系统** | ✅ Proxy-based (自动追踪) | ⚠️ 手动依赖数组 | ⚠️ Zone.js (性能开销) |

**选择理由**：
1. **Vue 3 Composition API**：比 Options API 更利于逻辑复用（本项目抽取了 `useProcessing` 等可组合函数），比 React Hooks 更直观（自动依赖追踪 vs 手动 `useCallback/useMemo`）。
2. **Naive UI**：Vue 3 原生组件库，TypeScript 类型完整，树摇友好，无需引入额外的 CSS-in-JS 方案。
3. **Vite**：开发服务器冷启动 < 1s，HMR 热更新 < 50ms，TypeScript 原生支持（esbuild 转译）。
4. **Pinia**：比 Vuex 更轻量（~1KB），完整的 TypeScript 类型推导，无需 mutations 样板代码。

### 3.4 图可视化：Cytoscape.js vs D3.js vs AntV G6

| 维度 | Cytoscape.js (本项目选择) | D3.js | AntV G6 |
|------|--------------------------|-------|---------|
| **图专用能力** | ✅ 原生图模型 (节点/边/布局) | ⚠️ 通用SVG/Canvas (需自建图模型) | ✅ 图专用 |
| **布局算法** | ✅ 10+ 内置 (dagre/cose/concentric等) | ⚠️ d3-force 需手动配置 | ✅ 8+ 内置 |
| **交互能力** | ✅ 拖拽/缩放/选择/右键菜单内置 | ⚠️ 需手动实现 | ✅ 内置 |
| **打包大小** | ~200KB (核心) | ~250KB | ~500KB (全量) |
| **TypeScript** | ⚠️ @types/cytoscape | ✅ v4+ 原生支持 | ✅ 原生支持 |
| **社区生态** | ⭐⭐⭐⭐ (生物信息学/知识图谱) | ⭐⭐⭐⭐⭐ (数据可视化) | ⭐⭐⭐ (阿里系) |

**选择理由**：
1. **原生图模型**：节点、边、布局是 Cytoscape.js 的一等公民，无需从 SVG/Canvas 基元构建图模型。
2. **开箱即用的交互**：拖拽、缩放、选择、右键菜单、动画等交互功能全部内置，只需 20 行配置（D3.js 需要 200+ 行手动实现）。
3. **多种布局**：dagre（层次）、cose（力导向）、concentric（同心圆）、breadthfirst、grid 五种布局一键切换。

### 3.5 任务队列：RQ vs Celery

| 维度 | RQ (本项目选择) | Celery |
|------|----------------|--------|
| **复杂度** | ⭐⭐⭐⭐⭐ (极简，~10行启动) | ⭐⭐ (复杂配置) |
| **依赖** | ✅ 仅需 Redis | ⚠️ Redis/RabbitMQ + Broker配置 |
| **监控面板** | ⚠️ rq-dashboard (可选) | ✅ Flower (功能丰富) |
| **任务取消** | ⚠️ 需手动实现 (本项目已实现) | ✅ revoke() 内置 |
| **序列化** | pickle (默认) | JSON/pickle/msgpack |
| **适用规模** | ⭐⭐⭐⭐ (中小规模，<10K tasks/day) | ⭐⭐⭐⭐⭐ (大规模) |

**选择理由**：
1. **极简主义**：本项目为知识图谱构建平台，任务量不大（文档上传 → 异步处理），RQ 的简洁性远胜 Celery 的复杂配置。
2. **与 Redis 深度集成**：项目同时使用 Redis 作为缓存和会话存储，RQ 天然集成无需额外 Broker。
3. **可维护性**：RQ 代码量小，源码可读，团队可在半天内完全理解其工作原理。

### 3.6 AI 集成架构：Factory + OpenAI Compatible Adapter

本项目的 AI 集成采用 **工厂模式 + 适配器模式** 的双层架构：

```
┌─────────────────────────────────┐
│       Application Code           │
│  (extractor.py, linker.py, ...) │
└───────────────┬─────────────────┘
                │ BaseAIClient.chat_completion()
┌───────────────▼─────────────────┐
│      AIProviderFactory           │  ← 工厂模式
│  create_client(provider, ...)   │
└───────────────┬─────────────────┘
        ┌───────┼───────────┐
        │       │           │
┌───────▼──┐ ┌──▼──────┐ ┌──▼──────────┐
│OpenAI    │ │Anthropic│ │OpenAICompat  │  ← 适配器模式
│Client    │ │Client   │ │ibleClient    │
│(原生SDK) │ │(原生SDK) │ │(统一适配)    │
└──────────┘ └─────────┘ └──┬───────────┘
                      ┌──────┼──────┬──────┐
                      │      │      │      │
                   DeepSeek Qwen  GLM  Moonshot
                   Ernie  MiniMax Doubao Ollama
```

**选择理由**：
1. **工厂模式**：运行时根据配置（Neo4j SystemConfig）创建不同客户端，前端无感切换 AI 提供商。
2. **OpenAI 兼容协议**：国产 AI 模型 80% 兼容 OpenAI API 格式，通过单一 `OpenAICompatibleClient` 可接入 6+ 种模型，维护成本极低。
3. **原生 SDK 保留**：OpenAI 和 Anthropic 使用原生 SDK，利用其高级功能（如 Anthropic 的 tool_use、OpenAI 的 structured outputs）。

---

## 四、面试问答

### Q1: 介绍一下 GraphForge 项目的整体架构？你是如何设计的？

**回答框架**：

GraphForge 采用**四层架构**：前端展示层（Vue 3）、API 网关层（FastAPI）、业务服务层（Services）、基础设施层（Infra + Neo4j + Redis）。

**设计理念**：
- **关注点分离**：路由层只做参数校验和响应格式化，业务逻辑在 Service 层，数据访问在 Infra 层
- **依赖倒置**：Service 层依赖 `BaseAIClient` 抽象接口而非具体实现，运行时通过 `AIProviderFactory` 注入具体客户端
- **配置外部化**：AI 提供商配置持久化到 Neo4j 而非硬编码，支持运行时热切换
- **异步优先**：所有 I/O 操作（文档解析、AI 调用、Neo4j 查询、Redis 队列）均使用 async/await

**核心数据流**：
```
文档上传 → RQ 异步队列 → Parser(解析) → AISegmenter(分块) → Extractor(LLM提取三元组)
→ Linker(实体消歧链接) → GraphService(Neo4j MERGE落库) → 前端可视化 + 问答
```

### Q2: GraphRAG 是什么？你的项目中如何实现的？

**回答框架**：

GraphRAG（Graph Retrieval-Augmented Generation）是 Microsoft 提出的将知识图谱与 LLM 结合的 RAG 变体。核心思想是：先构建知识图谱，再用图谱结构增强检索和生成。

**本项目实现**（9 阶段流水线）：
1. **Chunker (切分)**：滑动窗口语义切分，window=4句，step=2句
2. **Coref (指代消解)**：代词 → 全称映射，括号别名识别，3 种模式（rewrite/local/alias_only）
3. **Entity Linker (实体链接)**：BM25 + 向量混合检索，5 维精排打分，三档决策（自动接受/复核/拒绝）
4. **Claim Extractor (论断抽取)**：LLM 提取结构化三元组（subject-predicate-object-confidence）
5. **Theme Builder (主题构建)**：Louvain 多尺度社区检测（resolution 0.5/1.5），LLM 摘要生成
6. **Predicate Governor (谓词治理)**：自然语言谓词 → 5 种标准谓词映射，非标准谓词直接拒绝
7. **Graph Service (图谱存储)**：Neo4j MERGE 幂等写入，类型白名单过滤
8. **Query Service (查询)**：Local（图遍历 2-hop）+ Global（社区检索）+ Hybrid（0.6:0.4融合）
9. **Metrics (度量)**：覆盖率、准确率、一致性、连接性评估

**与传统 RAG 的区别**：
- 传统 RAG：向量检索 → Top-K 文本块 → LLM 生成
- GraphRAG：知识图谱构建 → 图结构检索（多跳关系、社区发现）→ 结构化上下文 → LLM 生成
- 优势：图谱能捕获实体间的多跳关系，提供更完整的上下文

### Q3: 你如何处理重复文档上传的幂等性问题？

**回答框架**：

**多层幂等保证**：

1. **内容哈希去重** (Service层)：上传时计算 SHA-256 哈希，查询 `MATCH (d:Document {content_hash: $hash})` 检查是否已存在，重复内容返回已有文档 ID。

2. **Neo4j MERGE 语义** (数据层)：
   ```cypher
   MERGE (c:Concept {name: $name})
   ON CREATE SET c += $properties, c.created_at = timestamp()
   ON MATCH SET c.updated_at = timestamp(), c.aliases = apoc.coll.union(c.aliases, $new_aliases)
   ```
   MERGE 保证相同 name 的节点不会重复创建，ON MATCH 子句实现别名追加而非覆盖。

3. **增量处理** (流水线层)：`ingest.py` 比较文档的 `processed_at` 时间戳，仅处理新增或更新的 Chunk 片段，避免全量重复处理。

### Q4: 12 种 AI 提供商的统一接口是如何设计的？

**回答框架**：

采用**工厂模式 + 策略模式 + 适配器模式** 的三重设计模式组合：

```python
# 抽象基类 - 策略模式
class BaseAIClient:
    def chat_completion(self, messages, temperature, **extra_params) -> str:
        raise NotImplementedError

# 工厂模式 - 根据配置创建客户端
class AIProviderFactory:
    _registry = {
        "openai":   OpenAIClient,        # 原生 SDK
        "anthropic": AnthropicClient,     # 原生 SDK
        "google":   GoogleGeminiClient,   # 适配器模式：OpenAI格式 → Gemini格式
        "deepseek": OpenAICompatibleClient,  # 适配器模式：OpenAI兼容协议
        "qwen":     OpenAICompatibleClient,
        # ... 6种国产模型均通过 OpenAICompatibleClient
        "mock":     MockClient
    }

    @classmethod
    def create_client(cls, provider, api_key, model, base_url) -> BaseAIClient:
        return cls._registry[provider](api_key, model, base_url)
```

**关键设计决策**：
1. **原生 SDK vs 兼容协议**：有官方 SDK 的用原生（OpenAI/Anthropic），其他用 OpenAI 兼容协议（一个 `OpenAICompatibleClient` 支持 8 种模型）
2. **Google Gemini 特殊处理**：Gemini 的 API 格式与 OpenAI 不完全兼容，通过继承 `OpenAICompatibleClient` 并覆盖 `_request()` 方法转换请求格式
3. **运行时热切换**：配置通过 Neo4j `SystemConfig` 节点持久化，`/settings/ai` 端点写入后，新 AI 调用立即使用新配置

### Q5: GraphForge 如何保证知识图谱的数据质量？

**回答框架**：

采用**四层递进过滤架构**：

| 层级 | 机制 | 位置 | 具体作用 |
|------|------|------|---------|
| Layer 1 | Prompt 限定 | `claim_extraction.txt` | 提示词明确限定"仅提取软件工程领域知识"，加入负面示例 |
| Layer 2 | Domain Filter | `domain_filter.py` (Stage 2) | 200+ 软件工程关键词库，BM25 + 向量双重验证，置信度阈值 0.3 |
| Layer 3 | Predicate Governor | `predicates.yaml` (Stage 5) | 自然语言谓词 → 5 种标准谓词映射，未匹配直接 REJECT |
| Layer 4 | Ontology Constraint | `ontology.yaml` (Stage 6) | 5 种实体白名单 + 5 种关系白名单 + 15 种源→谓词→目标 类型约束 |

**效果量化**（预计）：
- 无关实体数量减少 70-80%
- 关系类型从 14+ 种收敛到 5 种标准类型
- 知识卡片质量（覆盖率+准确率）显著提升

### Q6: 为什么选择 Neo4j 而不是 PostgreSQL 的图扩展（如 Apache AGE）？

**回答框架**：

1. **Cypher vs SQL 扩展**：Cypher 是专门为图查询设计的声明式语言，表达多跳关系查询远比 SQL CTE 递归自然。例如查询"Singleton Pattern 的所有相关知识点"：
   ```cypher
   // Cypher - 简洁直观
   MATCH (c:Concept {name: "Singleton Pattern"})-[r:BELONGS_TO*1..3]-(related)
   RETURN c, r, related
   ```
   ```sql
   -- SQL CTE - 复杂且性能差
   WITH RECURSIVE graph_traverse AS (
     SELECT * FROM edges WHERE source = 'Singleton Pattern'
     UNION ALL
     SELECT e.* FROM edges e JOIN graph_traverse g ON e.source = g.target
   ) SELECT * FROM graph_traverse WHERE depth <= 3
   ```

2. **图算法的原生支持**：Neo4j GDS 库提供 Louvain 社区检测、PageRank、Betweenness Centrality 等 50+ 种图算法，直接通过 Cypher 调用，无需将数据导出到 Python 再计算。

3. **GraphRAG 生态**：Microsoft 的 GraphRAG 官方推荐 Neo4j 作为图存储后端，`neo4j-graphrag` 库提供向量索引、混合搜索等开箱即用的集成。

4. **MERGE 语义**：Cypher 的 MERGE 是图数据库特有的幂等写入操作，PostgreSQL 的 UPSERT 需要手动处理节点和边的合并逻辑。

### Q7: 前端如何处理 Cytoscape.js 的大规模图谱渲染性能？

**回答框架**：

1. **节点数量限制**：`nodeLimit` 参数限制默认加载 100 个节点，用户可调整（`Graph.vue` 中的 `nodeLimit` ref）。

2. **虚拟化/分层渲染**：Cytoscape.js 使用 Canvas 渲染（非 DOM），天然支持万级节点的流畅交互。

3. **按需加载**：
   - 初始只加载核心节点（度数最高的 100 个）
   - 点击节点时动态加载邻居节点（`focusNode()` 方法）
   - 文档过滤器按 Document ID 筛选子图

4. **布局优化**：CoSE 布局使用 Web Worker 异步计算，不阻塞 UI 线程。

5. **样式缓存**：20+ 个 Cytoscape 样式选择器在 `renderGraph()` 中一次性注册，避免运行时样式计算。

### Q8: 如果让你优化 GraphForge 的某个模块，你会选哪个？如何优化？

**回答框架**（选一个体现深度的）：

**选择：Entity Linker 的候选检索性能**

**当前实现**：BM25 + 向量检索（各取 Top-20 → 合并取 Top-10 → 精排 5 维打分）

**优化方案**：
1. **向量索引加速**：集成 Neo4j 5.x 原生向量索引（`db.index.vector.createNodeIndex`），替代当前的内存向量计算，查询延迟从 O(N) 降到 O(log N)。
2. **候选剪枝**：在 BM25 和向量检索之前，增加类型预过滤（如候选实体类型必须与 mention 类型一致），减少无效候选。
3. **缓存热点实体**：对高频实体（如 "设计模式"、"敏捷开发"）的嵌入向量做 Redis 缓存，避免重复调用 Embedding API。
4. **批量 Embedding**：对多个 mention 的候选实体合并为单次 Embedding API 调用（batch_size=100），减少 API 调用次数。
5. **精排模型升级**：将 5 维线性打分升级为轻量级 Cross-Encoder（如 `all-MiniLM-L6-v2` 微调），在 GPU 上批量推理。

**预期效果**：链接延迟从 ~2s 降到 ~300ms，吞吐量提升 5-6x。

### Q9: GraphForge 系统中 Redis 的作用是什么？有哪些使用场景？

**回答框架**：

1. **任务队列 (RQ)**：文档处理异步任务的入队、调度、状态查询、取消。使用 Redis List 作为队列载体。

2. **配置缓存**：`config_service.py` 将运行时配置缓存到 Redis，避免每次请求都查询 Neo4j。

3. **连接测试**：`/settings/redis/health` 端点通过 `PING` 命令检测 Redis 连接状态。

4. **任务状态追踪**：前端轮询 `/ingest/status` 时，后端从 Redis 读取 RQ Job 的元数据（status, progress, result）。

**不使用 Redis 的场景**：
- 图数据查询 → Neo4j（图结构查询 Redis 无法胜任）
- 用户会话 → 可扩展但当前未实现（使用浏览器 localStorage）

### Q10: 你对 GraphForge 的未来演进有什么想法？

**回答框架**：

**短期（1-3 个月）**：
1. **Streaming 响应**：QA 接口支持 SSE（Server-Sent Events），实现 ChatGPT 式的流式输出
2. **跨文档知识融合**：Stage 4 Theme Builder 支持跨文档的主题构建（当前仅单文档）
3. **LangChain/LlamaIndex 集成**：利用成熟的 Agent 框架增强 QA 能力（工具调用、多步推理）

**中期（3-6 个月）**：
4. **多模态支持**：支持代码仓库（Git 历史 + AST 分析）、PPT、视频字幕的知识抽取
5. **知识图谱版本管理**：Git-like 的图谱变更历史，支持 diff 和 rollback
6. **协作功能**：多用户知识图谱协同编辑（CRDT 冲突解决）

**长期（6-12 个月）**：
7. **领域自适应**：从软件工程扩展到其他工程领域（机械、电子、土木），领域配置热切换
8. **图谱推理**：基于 Neo4j GDS 实现知识推理（传递性、对称性、组合性规则引擎）
9. **微服务拆分**：将 GraphRAG 流水线拆分为独立服务（Kubernetes + Knative 事件驱动）

---

## 附录

### A. 关键配置文件说明

| 文件 | 用途 | 关键配置项 |
|------|------|-----------|
| `ontology.yaml` | 本体定义 | 5 种实体类型 + 5 种关系类型 + 15 个知识分类 |
| `predicates.yaml` | 谓词白名单 | 5 种标准谓词 + 中英文映射表 |
| `thresholds.yaml` | 质量阈值 | 实体链接三档阈值 + Louvain 参数 + 向量配置 |
| `pytest.ini` | 测试配置 | 8 种测试标记 + 覆盖率配置 |
| `docker-compose.yml` | 容器编排 | Neo4j + Redis + API + Frontend |
| `nginx.conf` | 反向代理 | SPA fallback + /api 代理 |

### B. 测试策略

| 测试级别 | 标记 | 命令 | 覆盖内容 |
|---------|------|------|---------|
| 单元测试 | `unit` | `pytest -m unit` | 纯逻辑，无外部依赖 |
| 集成测试 | `integration` | `pytest -m integration` | Neo4j / Redis 依赖 |
| API 测试 | `api` | `pytest -m api` | FastAPI 路由端点 |
| GraphRAG | `graphrag` | `pytest -m graphrag` | 流水线各阶段 |
| 领域优化 | — | `python verify_quick.py` | 配置完整性无损检查 |

---

<div align="center">

**GraphForge** — Forging knowledge into connected graphs.

技术深度解析文档 v1.0 · 2026-06-29

</div>
