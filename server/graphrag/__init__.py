"""
GraphForge GraphRAG Module
==========================

基于 Neo4j GraphRAG 的知识图谱构建与检索模块 (v2.0)

Knowledge Graph construction and retrieval module based on the GraphRAG
architecture. This module implements a pipeline for building and querying
large-scale knowledge graphs from unstructured text.

Architecture / 架构说明::

    stages/         8 build stages implementation / 8 个构建阶段的实现
    models/         GraphRAG-specific data models / GraphRAG 专用数据模型
    config/         Configuration files (predicates whitelist, ontology) / 配置文件
    utils/          Utility functions / 工具函数
    api/            GraphRAG API endpoints / GraphRAG API 接口

Pipeline stages / 流水线阶段::

    1. SemanticChunker      Semantic text segmentation / 语义文本分块
    2. CoreferenceResolver  Coreference resolution / 指代消解
    3. EntityLinker         Entity linking and disambiguation / 实体链接与消歧
    4. ClaimExtractor       Fact extraction / 论断提取
    5. ThemeBuilder         Theme detection and hierarchy / 主题构建
    6. PredicateGovernor    Predicate governance / 谓词治理
    7. GraphService         Graph ingestion / 图谱写入
    8. QueryService         Graph query and retrieval / 图谱查询与检索
"""

__version__ = "2.0.0-alpha"

from graphrag.prompts.stages import (
    SemanticChunker,
    CoreferenceResolver,
    EntityLinker,
    ClaimExtractor,
    ThemeBuilder,
    PredicateGovernor,
    GraphService,
    QueryService,
    MetricsService
)

__all__ = [
    "SemanticChunker",
    "CoreferenceResolver",
    "EntityLinker",
    "ClaimExtractor",
    "ThemeBuilder",
    "PredicateGovernor",
    "GraphService",
    "QueryService",
    "MetricsService"
]
