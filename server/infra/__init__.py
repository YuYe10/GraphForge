"""
GraphForge Infrastructure Package
=================================

基础设施层，提供系统运行所需的底层支撑组件。

This package provides the foundational infrastructure components for the
GraphForge platform, including database connectivity, AI provider integration,
configuration management, task queuing, and file storage.

Components:
    config:         Application settings (loaded from environment variables)
    neo4j_client:   Neo4j graph database client with connection pooling
    ai_providers:   Multi-provider AI client factory (OpenAI, Anthropic, etc.)
    queue:          Redis-based task queue with graceful fallback to in-memory
    storage:        File storage utilities with checksum-based deduplication
"""

# Infrastructure modules

