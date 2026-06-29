"""
Document Data Models
====================

文档处理相关的数据模型定义，涵盖了从原始文档到结构化工件的完整表示。

Defines the Pydantic models for document processing, covering the full
representation from raw documents to structured artifacts (chunks and triplets).

Classes / 类说明:
    DocumentCreate:    Request model for creating a new document record
    Document:          Full document model with metadata and timestamps
    Chunk:             Text chunk extracted from a document during parsing
    Triplet:           Knowledge triplet (subject-predicate-object) extracted via AI
    AIExtractionRequest: Configuration for AI-powered document analysis
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class DocumentCreate(BaseModel):
    """
    Document creation request model.
    文档创建请求模型。

    Attributes:
        filename:   Original file name / 原始文件名
        checksum:   SHA256 checksum for deduplication / 用于去重的校验和
        kind:       Document type (pdf, md, docx, txt, etc.)
                    / 文档类型
        mime:       MIME type of the file / 文件的 MIME 类型
        size:       File size in bytes / 文件大小（字节）
        source_id:  Optional source identifier / 可选的来源标识
        meta:       Optional metadata dictionary / 可选的元数据字典
    """
    filename: str
    checksum: str
    kind: str = Field(..., description="Document type: pdf, md, docx, epub, html")
    mime: Optional[str] = None
    size: int
    source_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class Document(BaseModel):
    """
    Full document model with all properties and timestamps.
    完整的文档模型，包含所有属性和时间戳。

    Attributes:
        id:          Unique document identifier / 唯一文档标识符
        filename:    Original file name / 原始文件名
        checksum:    SHA256 checksum / 校验和
        kind:        Document type / 文档类型
        mime:        MIME type / MIME 类型
        size:        File size / 文件大小
        path:        Storage path / 存储路径
        source_id:   Source identifier / 来源标识
        meta:        Metadata dictionary / 元数据
        created_at:  Creation timestamp / 创建时间戳
        updated_at:  Last update timestamp / 最后更新时间戳
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    checksum: str
    kind: str
    mime: Optional[str] = None
    size: int
    path: Optional[str] = None
    source_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class Chunk(BaseModel):
    """
    Text chunk model — a segment of document text with positional metadata.
    文本块模型 — 文档文本的一个片段，附带位置元数据。

    Attributes:
        doc_id:   Document ID that this chunk belongs to / 所属文档 ID
        chunk_id: Unique chunk identifier / 唯一的块标识符
        text:     Chunk text content / 文本内容
        meta:     Positional metadata (page, section, offset, etc.)
                 / 位置元数据（页码、章节、偏移量等）
    """
    doc_id: str
    chunk_id: str
    text: str
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata: page, section, offset, etc."
    )


class Triplet(BaseModel):
    """
    Knowledge triplet (subject-predicate-object) model.
    知识三元组（主体-谓词-客体）模型。

    This is the fundamental unit of knowledge in the graph. Each triplet
    represents a single semantic relationship between two concepts.
    这是知识图谱中的基本知识单元，每个三元组表示两个概念之间的一个语义关系。

    Attributes:
        subject:    Source concept / 主体概念
        predicate:  Relationship type (e.g., "is_a", "contains", "affects")
                   / 关系类型
        object:     Target concept / 客体概念
        confidence: Extraction confidence score [0.0, 1.0] / 提取置信度
        evidence:   Supporting evidence (docId, chunkId, page, text excerpt)
                   / 支持证据
        doc_id:     Source document ID / 来源文档 ID
        chunk_id:   Source chunk ID / 来源文本块 ID
        context:    Contextual description of the relationship / 关系上下文说明
    """
    subject: str
    predicate: str
    object: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Evidence: docId, chunkId, page, offset"
    )
    doc_id: Optional[str] = None
    chunk_id: Optional[str] = None
    context: Optional[str] = Field(
        None,
        description="Contextual information about the relationship"
    )


class AIExtractionRequest(BaseModel):
    """
    AI extraction configuration model.
    AI 提取配置模型。

    Controls the behavior of AI-powered document analysis and knowledge extraction.
    控制 AI 驱动的文档分析和知识抽取的行为。

    Attributes:
        enable_ai_segmentation: Enable intelligent AI segmentation / 启用 AI 智能分词
        user_prompt:            Custom analysis prompt from user / 用户自定义分析提示词
        optimize_prompt:        Whether to optimize the user prompt via AI / 是否优化用户提示词
    """
    enable_ai_segmentation: bool = Field(
        False,
        description="Enable AI-powered intelligent segmentation"
    )
    user_prompt: Optional[str] = Field(
        None,
        description="User-defined analysis prompt"
    )
    optimize_prompt: bool = Field(
        True,
        description="Whether to optimize user prompt with AI"
    )
