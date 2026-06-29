"""
GraphForge API — FastAPI Application Entry Point
====================================================

GraphForge API 主入口 — FastAPI 应用程序启动和配置。

This module initializes and configures the FastAPI application, including:
- Application lifecycle management (startup/shutdown)
- Neo4j database connection initialization
- CORS middleware configuration
- API route registration
- Health check endpoints

Application architecture / 应用架构::

    main.py  (FastAPI app)
       │
       ├── routes/          API route handlers / API 路由处理
       │   ├── upload.py    File upload & document management / 文件上传
       │   ├── ingest.py    Document processing pipeline / 文档处理
       │   ├── graph.py     Knowledge graph query & CRUD / 图谱查询
       │   ├── settings.py  System configuration / 系统配置
       │   ├── knowledge_card.py  Concept management / 概念管理
       │   └── qa.py        Question answering / 智能问答
       │
       ├── services/        Business logic layer / 业务逻辑层
       ├── models/          Data models (Pydantic) / 数据模型
       └── infra/           Infrastructure / 基础设施层
           ├── neo4j_client.py   Neo4j graph database
           ├── ai_providers.py   Multi-provider AI clients
           ├── queue.py          Redis task queue
           ├── storage.py        File storage
           └── config.py         Application settings

Startup / 启动命令::

    # Development
    uvicorn server.main:app --reload

    # Production
    uvicorn server.main:app --host 0.0.0.0 --port 8000
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import upload, ingest, graph, settings, knowledge_card, qa
from infra.neo4j_client import neo4j_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup and shutdown events.
    应用程序生命周期的上下文管理器，处理启动和关闭事件。

    Startup (before yield) / 启动时::
        - Initialize Neo4j database connection / 初始化 Neo4j 连接
        - Schema constraints and indexes are created automatically

    Shutdown (after yield) / 关闭时::
        - Close Neo4j driver connection gracefully / 优雅关闭 Neo4j 连接

    The application starts even if Neo4j is unavailable (degraded mode).
    Database operations will fail with clear error messages.
    即使 Neo4j 不可用，应用也会启动（降级模式）。
    """
    # Startup: Initialize Neo4j connection / 启动时：初始化 Neo4j 连接
    try:
        neo4j_client.initialize()
        print("✅ Neo4j client initialized successfully")
    except Exception as e:
        print(f"⚠️  Warning: Failed to initialize Neo4j client: {e}")
        print("   The API will start but database operations will fail.")

    yield

    # Shutdown: Close connections / 关闭时：清理连接
    if neo4j_client.driver:
        neo4j_client.close()
        print("✅ Neo4j client closed")


app = FastAPI(
    title="GraphForge API",
    description=(
        "GraphForge — Knowledge Graph Platform / 知识图谱平台\n\n"
        "GraphForge converts unstructured documents into structured "
        "knowledge graphs using AI-powered entity extraction, "
        "intelligent entity linking, and Neo4j graph storage.\n\n"
        "Core features / 核心功能:\n"
        "- Document upload (PDF, Markdown, TXT, Word)\n"
        "- AI-powered knowledge extraction\n"
        "- Intelligent entity linking and alias merging\n"
        "- Interactive graph visualization\n"
        "- Knowledge card management\n"
        "- Multi-provider AI support (OpenAI, Anthropic, Qwen, etc.)"
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware — allows frontend applications to access the API
# CORS 中间件 — 允许前端应用访问 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers / 注册 API 路由
app.include_router(upload.router)           # /uploads
app.include_router(ingest.router)           # /ingest
app.include_router(graph.router)            # /graph
app.include_router(settings.router)         # /settings
app.include_router(knowledge_card.router)   # /knowledge-cards
app.include_router(qa.router)               # /qa


@app.get("/")
async def root():
    """
    Root endpoint — returns API metadata.
    根端点 — 返回 API 元信息。

    GET /
    """
    return {
        "name": "GraphForge API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """
    Health check endpoint for monitoring and load balancers.
    健康检查端点，用于监控和负载均衡器。

    GET /health

    Returns a simple {"status": "healthy"} response when the application
    is running. Note: this checks API availability, not Neo4j connectivity.
    """
    return {"status": "healthy"}
