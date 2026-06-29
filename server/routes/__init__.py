"""
GraphForge API Routes Package
=============================

API 路由层，定义所有 RESTful 接口端点。

This package contains all RESTful API route definitions for the GraphForge
platform. Each module corresponds to a specific domain and is registered as a
FastAPI APIRouter with appropriate prefixes and tags.

Routes:
    upload:          File upload, document management, text/URL ingestion
    ingest:          Document processing pipeline (parse, extract, link, ingest)
    graph:           Knowledge graph query, visualization, CRUD operations
    settings:        Application configuration, AI provider settings
    knowledge_card:  Knowledge card CRUD operations
    qa:              Intelligent Q&A using knowledge graph context
"""

# API routes

