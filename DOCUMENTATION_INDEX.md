# GraphForge 项目完整文档索引

## 📚 文档导航

本文档提供项目所有模块的文档索引，帮助开发者快速定位所需信息。

> **项目简介**: GraphForge 是一个面向《软件工程》课程的多模态知识图谱增量式构建平台，基于 GraphRAG 流水线实现从文档到结构化知识的全流程自动化。

---

## 🏗️ 项目架构概览

```
GraphForge/
├── DOCUMENTATION_INDEX.md       # 📖 本文档 — 文档总导航
├── README.md / README.en.md     # 项目简介与快速开始
├── LICENSE                      # MIT 开源协议
├── docker-compose.yml           # Docker 容器编排
│
├── server/                      # 后端服务 (Python 3.11 + FastAPI)
│   ├── main.py                 # FastAPI 应用入口
│   ├── pytest.ini              # pytest 配置 (标记/覆盖率)
│   ├── .coveragerc             # 覆盖率排除规则
│   ├── infra/                  # 基础设施层 — AI/Neo4j/队列/存储
│   │   └── README.md
│   ├── models/                 # 数据模型 (Pydantic)
│   │   └── README.md
│   ├── services/               # 业务服务层
│   │   └── README.md
│   ├── routes/                 # API 路由层 (RESTful)
│   │   └── README.md
│   ├── graphrag/               # GraphRAG 知识图谱流水线
│   │   ├── README.md           #   流水线总览文档
│   │   ├── api/                #   查询 / 反馈 API
│   │   ├── config/             #   本体 / 谓词 / 阈值配置 (YAML)
│   │   ├── models/             #   Chunk / Claim / Theme / Feedback
│   │   ├── prompts/            #   LLM 提示词模板 + 阶段实现
│   │   └── utils/              #   去重 / 验证 / 嵌入 / 领域过滤
│   └── tests/                  # 测试套件
│       ├── TEST_GUIDE.md       #   测试分类与运行指南
│       ├── QUICK_REFERENCE.md  #   常用命令速查
│       ├── TEST_FIXES_SUMMARY.md # 修复记录与经验总结
│       └── fixtures/           #   测试数据
│
└── app/vue/                     # 前端应用 (Vue 3 + TypeScript + Vite)
    ├── DEVELOPMENT_GUIDE.md    # 前端开发指南
    └── src/
        ├── README.md           # 前端架构说明
        ├── api/                # API 服务层
        ├── views/              # 页面组件 (8 个核心页面)
        ├── components/         # 通用组件
        ├── stores/             # Pinia 状态管理
        ├── router/             # Vue Router 路由
        ├── layouts/            # 布局组件
        └── i18n/               # 国际化 (中英双语)
```

---

## 📖 核心文档列表

### 🎯 快速入门

| 文档 | 路径 | 说明 |
|------|------|------|
| 项目 README (中文) | [README.md](README.md) | 项目简介、架构设计、安装运行指南 |
| 项目 README (英文) | [README.en.md](README.en.md) | English version of the README |
| Docker 编排 | [docker-compose.yml](docker-compose.yml) | 一键启动 Neo4j + Redis + 应用 |
| 前端开发指南 | [app/vue/DEVELOPMENT_GUIDE.md](app/vue/DEVELOPMENT_GUIDE.md) | 前端环境搭建与开发规范 |

---

### 🔧 后端文档

#### 基础设施层 (Infra)

| 文档 | 路径 | 内容 |
|------|------|------|
| Infra 模块说明 | [server/infra/README.md](server/infra/README.md) | AI 提供商、Neo4j 客户端、配置管理、队列、存储 |

**核心文件**:
| 文件 | 行数 | 职责 |
|------|------|------|
| `ai_providers.py` | ~616 | 12 个 AI 提供商统一接口 (OpenAI / Anthropic / 通义千问 / DeepSeek 等) |
| `neo4j_client.py` | ~594 | Neo4j 连接管理、批量操作、Schema 初始化 |
| `queue.py` | ~210 | Redis 异步任务队列 (RQ) |
| `storage.py` | ~55 | 文件上传存储服务 |
| `config.py` | ~40 | Pydantic Settings 配置管理 |

---

#### 数据模型层 (Models)

| 文档 | 路径 | 内容 |
|------|------|------|
| Models 模块说明 | [server/models/README.md](server/models/README.md) | 所有数据模型定义、验证规则与使用示例 |

**核心模型**:
- `Document` / `DocumentCreate` — 文档实体与创建请求
- `Chunk` — 文档切分后的文本块
- `Triplet` — 三元组 (知识图谱基本单元: 主体-谓词-客体)
- `AIExtractionRequest` — AI 提取配置
- `APIResponse` / `PaginatedResponse` — 统一 API 响应格式
- `SystemSettings` / `AIProviderSettings` / `ProcessingSettings` — 系统配置模型

---

#### 业务服务层 (Services)

| 文档 | 路径 | 内容 |
|------|------|------|
| Services 模块说明 | [server/services/README.md](server/services/README.md) | 业务逻辑服务详解与使用示例 |

**核心服务**:

| 服务 | 文件 | 核心类 | 职责 |
|------|------|--------|------|
| 文档解析 | `parser.py` | `ParserFactory` → `PDFParser` / `TxtParser` / `WordParser` / `MarkdownParser` | 多格式文档解析 (PDF / DOCX / TXT / MD) |
| AI 分段 | `ai_segmenter.py` | `AISegmenter` | 语义分块、文档结构分析、知识提取 |
| 知识抽取 | `extractor.py` | `TripletExtractor` | 基于 LLM 的三元组提取 |
| 实体链接 | `linker.py` | `EntityLinker` | 实体去重与链接 (`link_and_merge`) |
| 图谱服务 | `graph_service.py` | `GraphService` | Neo4j 节点/关系 CRUD |
| 智能问答 | `qa_service.py` | `QAService` | 基于图谱的上下文增强问答 |
| 配置管理 | `config_service.py` | `ConfigService` | 运行时配置读写 |

**服务依赖关系**:
```
DocumentParser → AISegmenter → TripletExtractor → EntityLinker → GraphService → QAService
```

---

#### API 路由层 (Routes)

| 文档 | 路径 | 内容 |
|------|------|------|
| Routes 模块说明 | [server/routes/README.md](server/routes/README.md) | 完整 API 参考、请求/响应格式、错误码、多语言示例 |

**API 模块一览**:

| 前缀 | 文件 | 核心功能 |
|------|------|----------|
| `/uploads` | `upload.py` | 文档上传、列表、详情、删除 |
| `/ingest` | `ingest.py` | 知识抽取任务提交、状态查询、取消 |
| `/graph` | `graph.py` | 图谱可视化数据、文档子图、概念子图、统计信息、节点 CRUD |
| `/qa` | `qa/ask` | 智能问答、历史记录、答案反馈 |
| `/knowledge-cards` | `knowledge_card.py` | 概念列表、概念详情、概念更新、关系创建 |
| `/settings` | `settings.py` | 系统设置读写、健康检查 |

> 📌 服务启动后访问 `http://localhost:8000/docs` 获得交互式 Swagger UI。

---

#### GraphRAG 模块

| 文档 | 路径 | 内容 |
|------|------|------|
| GraphRAG 说明 | [server/graphrag/README.md](server/graphrag/README.md) | 知识图谱增量构建流水线总览 |

**目录结构**:
| 子模块 | 路径 | 内容 |
|--------|------|------|
| API | `graphrag/api/` | 查询服务 (`query.py`) / 用户反馈 (`feedback.py`) |
| 配置 | `graphrag/config/` | 本体定义 (`ontology.yaml`) / 谓词规范 (`predicates.yaml`) / 阈值 (`thresholds.yaml`) |
| 模型 | `graphrag/models/` | Chunk / Claim / Theme / Feedback 数据结构 |
| 提示词 | `graphrag/prompts/` | LLM 提示词模板 (`.txt`) + 各阶段实现 (`.py`) |
| 工具 | `graphrag/utils/` | 论断去重、NLI 验证、嵌入生成、证据对齐、领域过滤、文本处理 |

**9 阶段流水线**:

| 阶段 | 名称 | 核心功能 |
|------|------|----------|
| Stage 0 | Chunker 篇章切分 | 语义边界识别、文档智能切分 |
| Stage 1 | Coref 指代消解 | 代词与引用解析、实体明确化 |
| Stage 2 | Entity Linker 实体链接 | 概念识别、消歧、链接到知识库 |
| Stage 3 | Claim Extractor 论断抽取 | 结构化三元组提取 (主体-谓词-客体) |
| Stage 4 | Theme Builder 主题构建 | Louvain 社区检测、层次聚类、摘要生成 |
| Stage 5 | Predicate Governor 谓词治理 | 关系规范化、同义谓词合并 |
| Stage 6 | Graph Service 图谱存储 | Neo4j MERGE 幂等落库 |
| Stage 7 | Query Service 查询服务 | 语义检索 + 图结构检索混合查询 |
| Stage 8 | Metrics Service 度量服务 | 覆盖率、准确率、一致性、连接性评估 |

---

#### 测试文档

| 文档 | 路径 | 内容 |
|------|------|------|
| 测试指南 | [server/tests/TEST_GUIDE.md](server/tests/TEST_GUIDE.md) | 测试分类、运行命令、标记说明、CI/CD 集成 |
| 快速参考 | [server/tests/QUICK_REFERENCE.md](server/tests/QUICK_REFERENCE.md) | 常用命令速查、故障排查 |
| 修复总结 | [server/tests/TEST_FIXES_SUMMARY.md](server/tests/TEST_FIXES_SUMMARY.md) | 单元测试修复记录、覆盖率分析、经验教训 |
| pytest 配置 | [server/pytest.ini](server/pytest.ini) | 标记定义、覆盖率范围、日志配置 |

**测试文件分类**:

| 类别 | 文件 | 说明 |
|------|------|------|
| 配置/Fixtures | `conftest.py` | 共享 fixtures 和测试环境初始化 |
| 快速验证 | `verify_quick.py` | 无需服务器 — 配置和文件完整性检查 |
| 领域优化 | `test_domain_optimization.py` | 领域过滤器验证 |
| 图谱集成 | `test_kg_optimization_integration.py` | 实体/关系类型验证 |
| 文档 (代码) | `test_documents_code.py` | 文档管理代码实现检查 |
| 文档 (Neo4j) | `test_documents_neo4j.py` | 需要 Neo4j — 数据库查询测试 |
| 文档 (全栈) | `test_documents_fullstack.py` | 需要服务器 — 文档管理全栈测试 |
| 文档 (最终) | `test_documents_final.py` | 需要服务器 — 文档管理 API 验证 |
| 文档 (集成) | `test_documents_integration.py` | 文档处理集成测试 |
| API 路由 | `test_api_routes.py` | FastAPI 端点集成测试 |
| API 图谱 | `test_graph_api.py` | 图谱可视化 API 测试 |
| 服务层 | `test_services.py` | 业务服务单元测试 |
| 基础设施 | `test_infra.py` / `test_infrastructure.py` | 基础设施层测试 |
| 覆盖率扩展 | `test_*_coverage*.py` | 覆盖率补充测试 |

**测试标记速查** (`pytest -m <mark>`):

| 标记 | 适用场景 |
|------|----------|
| `unit` | 快速纯逻辑测试，无需外部依赖 |
| `integration` | 需要 Neo4j / Redis |
| `api` | FastAPI 路由端点 |
| `graphrag` | GraphRAG 流水线 |
| `slow` | 耗时 > 5s 的测试 |
| `db` | 数据库相关 |
| `ai` | 需要 AI 服务调用 |

---

### 🎨 前端文档

| 文档 | 路径 | 内容 |
|------|------|------|
| 前端架构文档 | [app/vue/src/README.md](app/vue/src/README.md) | Vue 3 项目架构说明与目录结构 |
| 开发指南 | [app/vue/DEVELOPMENT_GUIDE.md](app/vue/DEVELOPMENT_GUIDE.md) | 环境搭建、开发规范、构建部署 |

**核心页面** (8 个):

| 页面 | 文件 | 功能 |
|------|------|------|
| Dashboard | `views/Dashboard.vue` | 仪表盘 — 统计数据总览 |
| Upload | `views/Upload.vue` | 文档上传 — 拖拽/批量上传 |
| Documents | `views/Documents.vue` | 文档管理 — 列表/搜索/删除 |
| Graph | `views/Graph.vue` | 知识图谱可视化 — Cytoscape.js 交互式图谱 (5 种布局) |
| Query | `views/Query.vue` | 智能问答 — 对话式知识检索 |
| KnowledgeCard | `views/KnowledgeCard.vue` | 知识卡片 — 概念浏览与详情 |
| Status | `views/Status.vue` | 处理状态 — 任务进度跟踪 |
| Settings | `views/Settings.vue` | 系统设置 — AI 提供商与参数配置 |

**通用组件**:

| 组件 | 文件 | 功能 |
|------|------|------|
| AppContent | `components/AppContent.vue` | 页面内容容器 |
| ProcessingFloater | `components/ProcessingFloater.vue` | 处理状态浮窗 |
| QADialog | `components/QADialog.vue` | 问答对话框 |

**技术栈亮点**:
- ✅ Vue 3 Composition API + TypeScript
- ✅ Naive UI 高质量组件库
- ✅ Cytoscape.js 图可视化 (5 种布局算法)
- ✅ Pinia 状态管理 (`app.ts` / `processing.ts`)
- ✅ Vue I18n 国际化 (中英双语)
- ✅ Vite 构建工具

---

## 🔍 按功能查找

### 文档上传和处理

1. 前端上传界面 — [app/vue/src/views/Upload.vue](app/vue/src/views/Upload.vue)
2. 上传 API — [server/routes/upload.py](server/routes/upload.py)
3. 文档解析服务 — [server/services/parser.py](server/services/parser.py)
4. AI 智能分段 — [server/services/ai_segmenter.py](server/services/ai_segmenter.py)
5. 路由文档 — [server/routes/README.md](server/routes/README.md) (Upload 部分)
6. 服务文档 — [server/services/README.md](server/services/README.md) (Parser + AISegmenter)

---

### 知识图谱构建

1. GraphRAG 流水线总览 — [server/graphrag/README.md](server/graphrag/README.md)
2. 阶段 Prompt 实现 — [server/graphrag/prompts/stages/](server/graphrag/prompts/stages/) (stage0–stage8)
3. 三元组提取 — [server/services/extractor.py](server/services/extractor.py)
4. 实体链接 — [server/services/linker.py](server/services/linker.py)
5. Neo4j 存储 — [server/infra/neo4j_client.py](server/infra/neo4j_client.py)
6. 工具函数 — [server/graphrag/utils/](server/graphrag/utils/) (去重、验证、嵌入等)
7. 配置文件 — [server/graphrag/config/](server/graphrag/config/) (本体、谓词、阈值)

---

### 图谱可视化

1. 前端可视化页面 — [app/vue/src/views/Graph.vue](app/vue/src/views/Graph.vue)
2. 图谱 API 路由 — [server/routes/graph.py](server/routes/graph.py)
3. Neo4j 查询客户端 — [server/infra/neo4j_client.py](server/infra/neo4j_client.py)
4. API 文档 — [server/routes/README.md](server/routes/README.md) (Graph 部分)
5. 前端开发指南 — [app/vue/DEVELOPMENT_GUIDE.md](app/vue/DEVELOPMENT_GUIDE.md) (图谱可视化章节)

---

### 智能问答

1. 问答界面 — [app/vue/src/views/Query.vue](app/vue/src/views/Query.vue)
2. QA 服务 — [server/services/qa_service.py](server/services/qa_service.py)
3. QA API 路由 — [server/routes/qa.py](server/routes/qa.py)
4. GraphRAG 查询 — [server/graphrag/api/query.py](server/graphrag/api/query.py)
5. API 文档 — [server/routes/README.md](server/routes/README.md) (QA 部分)

---

### AI 提供商集成

1. AI 提供商实现 — [server/infra/ai_providers.py](server/infra/ai_providers.py)
2. Infra 文档 — [server/infra/README.md](server/infra/README.md) (AI Providers 章节)
3. 配置管理 — [server/infra/config.py](server/infra/config.py)
4. 前端设置页 — [app/vue/src/views/Settings.vue](app/vue/src/views/Settings.vue)

---

## 🎓 学习路径推荐

### 新手入门 (第 1–3 天)

1. 阅读项目 README — [README.md](README.md)
2. 按 README 步骤启动项目 (Docker 或本地)
3. 阅读前端架构 — [app/vue/src/README.md](app/vue/src/README.md)
4. 阅读数据模型 — [server/models/README.md](server/models/README.md)
5. 运行快速验证 — `cd server && python tests/verify_quick.py`

---

### 后端开发 (第 4–7 天)

1. **基础设施**:
   - Infra 模块 — [server/infra/README.md](server/infra/README.md)
   - 了解 AI 提供商接入方式
   - 学习 Neo4j Cypher 查询

2. **业务服务**:
   - Services 模块 — [server/services/README.md](server/services/README.md)
   - 理解文档处理全流程 (解析 → 分段 → 抽取 → 链接 → 存储)
   - 学习工厂模式和依赖注入

3. **API 开发**:
   - Routes 模块 — [server/routes/README.md](server/routes/README.md)
   - 使用 Swagger UI (`http://localhost:8000/docs`) 交互调试
   - 编写 API 测试

---

### 前端开发 (第 8–10 天)

1. **Vue 基础**:
   - 开发指南 — [app/vue/DEVELOPMENT_GUIDE.md](app/vue/DEVELOPMENT_GUIDE.md)
   - 前端架构 — [app/vue/src/README.md](app/vue/src/README.md)
   - 学习 Composition API + TypeScript 开发规范

2. **核心功能**:
   - 图谱可视化 — Cytoscape.js 集成实践
   - 状态管理 — Pinia stores (`app.ts`, `processing.ts`)
   - 组件开发 — Naive UI 组件使用

3. **样式与交互**:
   - SCSS 编写规范
   - 响应式布局
   - 国际化 (i18n) 配置

---

### GraphRAG 深入 (第 11–14 天)

1. 流水线总览 — [server/graphrag/README.md](server/graphrag/README.md)
2. 各阶段实现 — [server/graphrag/prompts/stages/](server/graphrag/prompts/stages/)
3. 配置文件研读 — [server/graphrag/config/](server/graphrag/config/)
4. 工具函数 — [server/graphrag/utils/](server/graphrag/utils/)
5. 测试与调试:
   - 运行 GraphRAG 测试 — `pytest -m graphrag -v`
   - 查看覆盖率报告 — `pytest --cov=graphrag --cov-report=html`

---

## 📝 文档编写规范

### 模块文档结构

每个模块的 README.md 应包含:

```markdown
# 模块名称

## 📋 模块概述
- 核心职责
- 主要功能

## 📁 模块结构
- 文件列表
- 目录说明

## 🔧 核心类/函数
- API 文档
- 使用示例

## 💡 使用场景
- 典型用例
- 最佳实践

## 🧪 测试
- 测试覆盖
- 测试示例

## 📚 相关文档
- 链接到其他文档
```

---

## 🔄 文档维护

### 更新频率

- **主 README**: 每个版本发布时更新
- **API 文档** ([server/routes/README.md](server/routes/README.md)): 代码变更后同步更新
- **模块 README**: 模块重构时同步更新
- **测试文档**: 测试策略变更后更新

### 贡献指南

1. 发现文档问题 → 提 Issue
2. 想改进文档 → 提 PR
3. 新增功能 → 同步更新对应模块的 README
4. 重构代码 → 检查相关文档是否需要更新

---

## 🔗 外部资源

### 技术文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Vue 3 官方文档](https://vuejs.org/)
- [Neo4j Cypher 文档](https://neo4j.com/docs/)
- [Pydantic v2 文档](https://docs.pydantic.dev/)
- [Cytoscape.js 文档](https://js.cytoscape.org/)
- [Naive UI 文档](https://www.naiveui.com/)
- [Pinia 状态管理](https://pinia.vuejs.org/)

### 相关论文

- [Microsoft GraphRAG](https://microsoft.github.io/graphrag/) — 图增强检索生成
- [From Local to Global: A Graph RAG Approach to Query-Focused Summarization](https://arxiv.org/abs/2404.16130)

---

## 📞 获取帮助

- **问题反馈**: GitHub Issues
- **功能建议**: GitHub Discussions
- **紧急问题**: 联系项目维护者

---

<div align="center">

**GraphForge** — Forging knowledge into connected graphs.

Made with ❤️ by the GraphForge Team

</div>
