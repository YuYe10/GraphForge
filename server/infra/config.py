"""
Application Configuration Management
=====================================

应用配置管理模块，基于 Pydantic Settings 从环境变量加载配置。

This module manages all application configuration using Pydantic Settings.
Configuration is loaded from environment variables and/or a .env file at
application startup. It covers database connections, AI provider settings,
GraphRAG parameters, and file upload paths.

Architecture / 架构说明::

    ┌─────────────────────┐
    │     Settings()      │  ← Global singleton / 全局单例
    │  (Pydantic v2)      │
    ├─────────────────────┤
    │  .env file          │  ← Sensible defaults / 合理默认值
    │  env vars           │  ← Override priority / 覆盖优先级
    └─────────────────────┘

Configuration sections:
    - Neo4j:        Graph database connection
    - Redis:        Task queue and caching
    - AI Provider:  LLM service configuration (multi-provider)
    - File Upload:  Upload directory
    - GraphRAG:     GraphRAG v2.0 pipeline settings
"""
import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    从环境变量加载的应用程序配置。

    All configuration values have sensible defaults and can be overridden
    via a .env file or system environment variables. Pydantic v2's
    BaseSettings handles type coercion and validation automatically.
    所有配置值都有合理的默认值，可通过 .env 文件或系统环境变量覆盖。

    Attributes:
        # === Neo4j Configuration / 数据库配置 ===
        neo4j_uri:  Neo4j connection URI (default: bolt://localhost:7687)
        neo4j_user: Neo4j username (default: neo4j)
        neo4j_pass: Neo4j password (default: neo4j1234)

        # === Redis Configuration / 缓存与队列配置 ===
        redis_url:            Redis connection URL
        redis_password:       Redis password (must set in production)
        redis_db:             Redis database number
        redis_max_connections: Connection pool size
        redis_socket_timeout:  Socket timeout in seconds
        redis_default_ttl:    Default TTL for cache keys (24h)
        redis_key_prefix:     Key namespace prefix

        # === AI Provider Configuration / AI 服务商配置 ===
        ai_provider:  AI provider selection (openai, anthropic, google, etc.)
        ai_api_key:   API key for the selected provider
        ai_model:     Model name override
        ai_base_url:  Custom API base URL

        # === Legacy Compatibility / 向后兼容配置 ===
        openai_api_key:   OpenAI API key (legacy)
        openai_model:     OpenAI model name
        openai_base_url:  OpenAI API base URL
        ollama_base_url:  Ollama local server URL
        ollama_model:     Ollama model name

        # === File Upload / 文件上传配置 ===
        upload_dir:  Upload directory path
        api_host:    API server host
        api_port:    API server port

        # === GraphRAG v2.0 / 图谱增强检索配置 ===
        enable_neo4j_graphrag:      Enable Neo4j GraphRAG features
        enable_vector_search:       Enable vector search capabilities
        llm_model:                  LLM model for GraphRAG
        embedding_model:            Embedding model for vectors
        embedding_dimension:        Vector embedding dimension
        allowed_node_types:         Allowed node type whitelist
        allowed_relations:          Allowed relationship type whitelist
        entity_link_accept_threshold: Entity linking acceptance threshold
        claim_confidence_threshold:   Claim confidence threshold
        vector_search_top_k:        Vector search top-K results
        community_algorithm:        Community detection algorithm
        predicate_governance_enabled: Enable predicate governance
    """

    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ============================================
    # Neo4j Configuration / Neo4j 图数据库配置
    # ============================================
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_pass: str = "neo4j1234"

    # ============================================
    # Redis Configuration / Redis 缓存与队列配置
    # ============================================
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None          # Redis 密码（生产环境必须设置）
    redis_db: int = 0                             # Redis 数据库编号（0-15）
    redis_max_connections: int = 20               # 连接池最大连接数
    redis_socket_timeout: int = 5                 # Socket 超时（秒）
    redis_socket_connect_timeout: int = 3          # 连接超时（秒）
    redis_retry_on_timeout: bool = True           # 超时自动重试
    redis_health_check_interval: int = 30         # 健康检查间隔（秒）
    redis_default_ttl: int = 86400                # 默认 key 过期时间（秒），24小时
    redis_key_prefix: str = "graphforge"          # Key 前缀命名空间

    # ============================================
    # AI Provider Configuration / AI 服务提供商配置
    # ============================================
    ai_provider: Literal[
        "openai",           # OpenAI GPT
        "anthropic",        # Anthropic Claude
        "google",           # Google Gemini
        "deepseek",         # DeepSeek
        "qwen",             # 阿里云通义千问
        "glm",              # 智谱AI (GLM)
        "moonshot",         # 月之暗面 Kimi
        "ernie",            # 百度文心一言
        "minimax",          # MiniMax
        "doubao",           # 字节豆包
        "ollama",           # Ollama 本地模型
        "mock"              # Mock 模式（测试用）
    ] = "mock"

    # 通用 AI 配置（推荐使用这三个通用字段配置 AI）
    ai_api_key: Optional[str] = None        # AI服务的API密钥
    ai_model: Optional[str] = None          # 模型名称（留空则使用默认）
    ai_base_url: Optional[str] = None       # 自定义API地址（留空则使用默认）

    # === 以下为兼容性配置（旧版本） ===
    # OpenAI-specific configuration (legacy)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: Optional[str] = None

    # Ollama-specific configuration (legacy)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # File Upload Configuration
    upload_dir: str = "./uploads"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # ============================================
    # GraphRAG Configuration (v2.0-GraphRAG)
    # ============================================

    # GraphRAG feature toggles / 功能开关
    enable_neo4j_graphrag: bool = True
    enable_vector_search: bool = True

    # Model configuration / 模型配置
    llm_model: str = "qwen-plus"
    embedding_model: str = "text-embedding-v3"
    embedding_dimension: int = 1536  # OpenAI text-embedding-3-small 维度

    # Node type whitelist / 允许的节点类型白名单
    allowed_node_types: list[str] = [
        "Concept", "Person", "Method", "Tool", "Metric",
        "Chunk", "Claim", "Theme", "Document", "Topic"
    ]

    # Relation type whitelist / 允许的关系类型白名单
    allowed_relations: list[str] = [
        "IS_A", "PART_OF", "USES", "IMPLEMENTED_BY", "CREATES",
        "DERIVES_FROM", "CONTAINS", "BELONGS_TO", "SUPPORTS",
        "CONTRADICTS", "CAUSES", "COMPARES_WITH", "CONDITIONS",
        "PURPOSE", "MENTIONS", "CONTAINS_CLAIM", "BELONGS_TO_THEME",
        "EVIDENCE_FROM", "SIMILAR_TO"
    ]

    # Threshold configuration / 阈值配置
    entity_link_accept_threshold: float = 0.85  # 实体链接接受阈值
    entity_link_review_threshold: float = 0.65  # 实体链接复核阈值
    claim_confidence_threshold: float = 0.7     # 论断置信度阈值

    # Vector search configuration / 向量检索配置
    vector_search_top_k: int = 5                # 向量检索 Top-K
    vector_search_threshold: float = 0.7        # 向量相似度阈值

    # Community detection configuration / 社区检测配置
    community_algorithm: str = "louvain"        # 社区检测算法: louvain | leiden
    community_min_size: int = 3                 # 最小社区规模

    # Predicate governance configuration / 谓词治理配置
    predicate_governance_enabled: bool = True   # 是否启用谓词治理
    predicate_mapping_file: str = "graphrag/config/predicates.yaml"
    ontology_config_file: str = "graphrag/config/ontology.yaml"

    # Build version configuration / 构建版本配置
    build_version_prefix: str = "v2.0"          # 构建版本前缀


# Global singleton: shared across the application
# 全局单例：在整个应用中共享
settings = Settings()
