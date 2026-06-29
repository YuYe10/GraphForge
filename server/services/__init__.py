"""
GraphForge Services Package
===========================

业务逻辑服务层，封装了所有核心业务处理逻辑。

This package contains all business logic services for the GraphForge platform.
Each service encapsulates a specific domain responsibility, providing a clean
abstraction layer between the API routes and infrastructure components.

Services:
    parser:          Document parsing (PDF, Markdown, TXT, Word) with smart chunking
    extractor:       Triplet extraction from text using LLM (subject-predicate-object)
    linker:          Entity linking and alias merging with bilingual support
    graph_service:   Knowledge graph ingestion (concepts, relationships, topics)
    config_service:  Runtime configuration management (stored in Neo4j)
    qa_service:      Intelligent Q&A using knowledge graph context
    ai_segmenter:    AI-powered document segmentation and knowledge extraction
"""

# Service modules

