"""
File Upload and Document Management API Routes
===============================================

文件上传与文档管理 API 路由，支持多种来源的文档导入和处理。

Provides endpoints for document upload, management, and processing. Supports
multiple ingestion sources:

Data sources / 数据来源::

    ├── POST /uploads              File upload / 文件上传
    ├── POST /uploads/text         Text paste / 文本粘贴
    ├── POST /uploads/url          URL scrape / 网页抓取
    └── POST /uploads/process      Upload + auto-process / 上传并自动处理

Endpoints / 接口列表::

    # Document CRUD / 文档 CRUD
    POST   /uploads              Upload a file / 上传文件
    GET    /uploads               List documents / 获取文档列表
    GET    /uploads/{id}          Get document details / 获取文档详情
    GET    /uploads/{id}/file     Download/preview file / 下载文件
    DELETE /uploads/{id}          Delete document + graph data / 删除文档

    # Processing / 处理
    POST   /uploads/process       Upload and auto-process / 上传并自动处理
    GET    /uploads/status/{id}   Get processing status / 获取处理状态

    # Alternative inputs / 其他输入方式
    POST   /uploads/text          Upload text content / 上传文本
    POST   /uploads/url           Upload URL content / 上传网页内容

Supported file types / 支持的文件类型::
    PDF, Markdown, TXT, Word (DOC/DOCX)
"""
import uuid
import hashlib
import json
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    BackgroundTasks,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel

from infra.neo4j_client import neo4j_client
from infra.storage import Storage
from services.parser import ParserFactory
from services.extractor import TripletExtractor
from services.linker import EntityLinker
from services.graph_service import GraphService
from services.ai_segmenter import AISegmenter
from models.document import AIExtractionRequest
from infra.queue import get_queue
from infra.config import settings

router = APIRouter(prefix="/uploads", tags=["uploads"])

storage = Storage()
extractor = TripletExtractor()
linker = EntityLinker()
graph_service = GraphService()

# Initialize AI segmenter (optional — based on configured AI provider)
# 初始化 AI 分词器（可选——基于配置的 AI 提供商）
try:
    ai_segmenter = AISegmenter()
except ValueError as e:
    ai_segmenter = None
    print(f"⚠️  AI segmentation disabled: {str(e)}")

# Initialize Redis queue / 初始化 Redis 队列
queue = get_queue()

# Fallback job storage (used when Redis is not available)
# 备用的内存任务存储（Redis 不可用时使用）
processing_jobs = {}

ALLOWED_EXTENSIONS = {
    ".pdf": "pdf",
    ".md": "md",
    ".markdown": "md",
    ".txt": "txt",
    ".doc": "word",
    ".docx": "word",
}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/markdown",
    "text/x-markdown",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument"
    ".wordprocessingml.document",
    "application/octet-stream",  # Fallback used by some browsers
}

SUPPORTED_TYPES_LABEL = "PDF, Markdown, TXT, Word (DOC/DOCX)"


def get_document_kind(filename: str) -> str:
    """
    Determine document kind from a filename based on extension.
    根据文件名后缀确定文档类型。

    Args:
        filename:  Original filename / 原始文件名

    Returns:
        Document kind string (pdf, md, txt, word), or "unknown"
    """
    ext = Path(filename).suffix.lower()
    return ALLOWED_EXTENSIONS.get(ext, "unknown")


def validate_content_type(content_type: Optional[str]) -> None:
    """
    Validate the MIME type of an uploaded file.
    验证上传文件的 MIME 类型。

    Raises HTTPException (422) if the MIME type is not in the allowlist.

    Args:
        content_type:  MIME type string from the upload / MIME 类型字符串

    Raises:
        HTTPException 422: If content type is not allowed
    """
    if not content_type:
        return
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unsupported MIME type: {content_type}. "
                f"Allowed types: {SUPPORTED_TYPES_LABEL}"
            ),
        )


@router.post("", response_model=dict)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file and create a document record in Neo4j.
    上传文件并在 Neo4j 中创建文档记录。

    POST /uploads

    The file is saved to the uploads directory with a checksum-based
    filename. If a document with the same checksum already exists,
    returns the existing document ID with status "duplicate".

    Args:
        file:  Uploaded file (multipart/form-data) / 上传的文件

    Returns:
        Dict with documentId, filename, checksum, status, and path
    """
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # Determine document kind from extension / 根据扩展名确定文档类型
    kind = get_document_kind(file.filename)
    if kind == "unknown":
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unsupported file type: "
                f"{Path(file.filename).suffix or 'unknown'}. "
                f"Allowed types: {SUPPORTED_TYPES_LABEL}"
            ),
        )

    validate_content_type(file.content_type)

    # Save file and get checksum / 保存文件并获取校验和
    file_path, checksum = await storage.save_file(
        content, file.filename
    )

    # Check for duplicate by checksum / 通过校验和检查重复
    existing_docs = neo4j_client.execute_query(
        "MATCH (d:Document {checksum: $checksum}) "
        "RETURN d.id as id LIMIT 1",
        {"checksum": checksum},
    )

    if existing_docs:
        return {
            "documentId": existing_docs[0]["id"],
            "filename": file.filename,
            "checksum": checksum,
            "status": "duplicate",
            "message": "Document already exists",
        }

    # Create document record in Neo4j / 在 Neo4j 中创建文档记录
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"

    neo4j_client.create_document(
        doc_id=doc_id,
        filename=file.filename,
        checksum=checksum,
        kind=kind,
        size=len(content),
        mime=file.content_type,
        meta={"path": file_path},
    )

    return {
        "documentId": doc_id,
        "filename": file.filename,
        "checksum": checksum,
        "status": "uploaded",
        "path": file_path,
    }


@router.get("")
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    sort_by: str = "created_at",  # "created_at" or "filename"
):
    """
    List all uploaded documents with optional pagination and sorting.
    获取所有已上传的文档列表，支持分页和排序。

    GET /uploads

    Returns each document with its processing status, chunk/concept/claim
    counts, and checksum for duplicate detection.

    Args:
        skip:     Number of documents to skip (offset) / 跳过的文档数
        limit:    Maximum documents to return (max 100) / 最大返回数
        sort_by:  Sort field: "created_at" (default) or "filename"
                 / 排序字段

    Returns:
        Dict with total count and documents list
    """
    skip = max(0, skip)
    limit = min(limit, 100)

    # Get total count / 获取总数
    total_result = neo4j_client.execute_query(
        "MATCH (d:Document) RETURN count(d) as total"
    )
    total = total_result[0]["total"] if total_result else 0

    # Build ORDER BY clause / 构建排序子句
    order_clause = "d.created_at DESC"
    if sort_by == "filename":
        order_clause = "d.filename ASC"

    query = f"""
    MATCH (d:Document)
    OPTIONAL MATCH (d)-[rel]-(related)
    WITH d, count(DISTINCT rel) as rel_count,
         count(DISTINCT CASE WHEN 'Chunk' IN labels(related)
             THEN related END) as chunk_count,
         count(DISTINCT CASE WHEN 'Concept' IN labels(related)
             THEN related END) as concept_count,
         count(DISTINCT CASE WHEN 'Claim' IN labels(related)
             THEN related END) as claim_count
    RETURN DISTINCT
        d.id AS id,
        d.filename AS filename,
        d.kind AS kind,
        d.size AS size,
        d.created_at AS created_at,
        d.updated_at AS updated_at,
        d.checksum AS checksum,
        chunk_count,
        concept_count,
        claim_count,
        rel_count,
        coalesce(d.processing_status, "") AS processing_status
    ORDER BY {order_clause}
    SKIP {skip}
    LIMIT {limit}
    """

    results = neo4j_client.execute_query(query)

    documents = []
    for row in results:
        chunk_count = row.get("chunk_count", 0) or 0
        rel_count = row.get("rel_count", 0) or 0
        persisted_status = row.get("processing_status") or ""
        processing_status = persisted_status or (
            "completed" if chunk_count > 0 or rel_count > 0
            else "uploaded"
        )

        documents.append({
            "id": row.get("id"),
            "filename": row.get("filename"),
            "kind": row.get("kind"),
            "size": row.get("size"),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
            "checksum": row.get("checksum"),
            "chunk_count": chunk_count,
            "concept_count": row.get("concept_count", 0) or 0,
            "claim_count": row.get("claim_count", 0) or 0,
            "processing_status": processing_status,
        })

    return {"total": total, "documents": documents}


@router.get("/{document_id}")
async def get_document(document_id: str):
    """
    Get detailed information about a document.
    获取文档详细信息，包括统计信息和关联主题。

    GET /uploads/{document_id}

    Returns document metadata, statistics (chunks, concepts, claims,
    relations), and any associated themes.

    Args:
        document_id:  Document ID / 文档 ID

    Returns:
        Dict with document properties, statistics, and themes

    Raises:
        404: If document not found
    """
    # Get basic document info / 获取基本文档信息
    doc_result = neo4j_client.execute_query(
        "MATCH (d:Document {id: $doc_id}) RETURN d",
        {"doc_id": document_id},
    )

    if not doc_result:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    doc_data = doc_result[0]["d"]

    # Get statistics / 获取统计信息
    stats_query = """
    MATCH (d:Document {id: $doc_id})
    OPTIONAL MATCH (d)-[rel]-(related)
    WITH d,
         count(DISTINCT CASE WHEN 'Chunk' IN labels(related)
             THEN related END) as chunk_count,
         count(DISTINCT CASE WHEN 'Concept' IN labels(related)
             THEN related END) as concept_count,
         count(DISTINCT CASE WHEN 'Claim' IN labels(related)
             THEN related END) as claim_count,
         count(DISTINCT rel) as relation_count
    RETURN
        chunk_count,
        concept_count,
        claim_count,
        relation_count
    """

    stats_result = neo4j_client.execute_query(
        stats_query, {"doc_id": document_id}
    )
    statistics = (
        {
            "chunk_count": stats_result[0].get("chunk_count", 0) or 0,
            "concept_count": stats_result[0].get(
                "concept_count", 0
            )
            or 0,
            "claim_count": stats_result[0].get("claim_count", 0) or 0,
            "relation_count": stats_result[0].get(
                "relation_count", 0
            )
            or 0,
        }
        if stats_result
        else {
            "chunk_count": 0,
            "concept_count": 0,
            "claim_count": 0,
            "relation_count": 0,
        }
    )

    # Get associated themes / 获取关联的主题
    themes_query = """
    MATCH (d:Document {id: $doc_id})
    MATCH (d)<-[:BELONGS_TO]-(c:Concept)
    MATCH (c)-[:BELONGS_TO_THEME]->(t:Theme)
    RETURN DISTINCT
        t.id AS id,
        t.label AS label,
        t.level AS level,
        t.member_count AS member_count,
        t.summary AS summary
    LIMIT 20
    """

    themes_result = neo4j_client.execute_query(
        themes_query, {"doc_id": document_id}
    )
    themes = [
        {
            "id": t.get("id"),
            "label": t.get("label"),
            "level": t.get("level"),
            "member_count": t.get("member_count"),
            "summary": t.get("summary"),
        }
        for t in themes_result
    ]

    return {
        "id": doc_data.get("id"),
        "filename": doc_data.get("filename"),
        "kind": doc_data.get("kind"),
        "size": doc_data.get("size"),
        "created_at": doc_data.get("created_at"),
        "updated_at": doc_data.get("updated_at"),
        "checksum": doc_data.get("checksum"),
        "mime": doc_data.get("mime"),
        "meta": doc_data.get("meta", {}),
        "statistics": statistics,
        "themes": themes,
        "processing_status": (
            "completed" if statistics["chunk_count"] > 0
            else "uploaded"
        ),
    }


@router.get("/{document_id}/file")
async def download_document_file(document_id: str):
    """
    Download or preview a document's original file.
    下载或预览文档原文件，供前端内嵌查看。

    GET /uploads/{document_id}/file

    Supports inline viewing for PDF, TXT, MD and other browser-renderable
    formats. Uses Content-Disposition: inline with UTF-8 filename encoding
    for non-ASCII filenames (Chinese, etc.).

    Args:
        document_id:  Document ID / 文档 ID

    Returns:
        FileResponse with the original file content

    Raises:
        404: If document or file not found
    """
    result = neo4j_client.execute_query(
        "MATCH (d:Document {id: $doc_id}) RETURN d",
        {"doc_id": document_id},
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    doc_node = result[0]["d"]

    # Parse meta — compatible with string/JSON/dict formats
    # 解析 meta，兼容字符串/JSON/字典格式
    raw_meta = doc_node.get("meta")
    meta = {}
    if isinstance(raw_meta, dict):
        meta = raw_meta
    elif isinstance(raw_meta, str):
        try:
            meta = json.loads(raw_meta)
            if isinstance(meta, str):  # Double-encoded / 双重编码
                meta = json.loads(meta)
        except Exception:
            meta = {}

    file_path = (
        meta.get("path") if isinstance(meta, dict) else None
    )

    # Fallback: find by checksum if path not in meta
    # 如果 meta 没有路径，尝试根据 checksum 找文件
    if not file_path:
        checksum = doc_node.get("checksum")
        if checksum:
            existing = storage.file_exists(checksum)
            if existing:
                file_path = existing

    if not file_path:
        raise HTTPException(
            status_code=404,
            detail="File path not found",
        )

    abs_path = Path(file_path)
    if not abs_path.is_absolute():
        abs_path = (
            Path(settings.upload_dir) / file_path
            if not file_path.startswith(
                str(Path(settings.upload_dir))
            )
            else Path(file_path)
        )
        if not abs_path.exists():
            abs_path = Path.cwd() / file_path

    if not abs_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found on server",
        )

    media_type = (
        doc_node.get("mime") or "application/octet-stream"
    )
    filename = doc_node.get("filename") or abs_path.name

    # URL-encode for non-ASCII (Chinese) filename support
    # URL 编码处理非 ASCII 文件名（中文等）
    encoded_filename = quote(filename)

    headers = {
        "Content-Disposition": (
            f"inline; filename*=UTF-8''{encoded_filename}"
        )
    }

    return FileResponse(
        abs_path,
        media_type=media_type,
        filename=filename,
        headers=headers,
    )


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document, its file, and all associated graph data.
    删除文档、其文件及所有关联的图谱数据。

    DELETE /uploads/{document_id}

    Cascade / 级联删除::
        1. Remove the physical file from uploads/
        2. Delete the Document node and all its relationships
        3. Recursively delete orphan nodes (nodes with no remaining edges)

    This ensures graph integrity by cleaning up all data related to
    the document.

    Args:
        document_id:  Document ID / 文档 ID

    Returns:
        Dict with success status, counts of deleted edges and orphan nodes
    """
    # Fetch document metadata / 获取文档元数据
    result = neo4j_client.execute_query(
        "MATCH (d:Document {id: $doc_id}) RETURN d",
        {"doc_id": document_id},
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    doc_data = result[0]["d"]

    # Resolve file path from meta / 从 meta 中解析文件路径
    raw_meta = doc_data.get("meta")
    meta: dict = {}
    if isinstance(raw_meta, dict):
        meta = raw_meta
    elif isinstance(raw_meta, str):
        try:
            parsed = json.loads(raw_meta)
            if isinstance(parsed, dict):
                meta = parsed
            elif isinstance(parsed, str):
                meta = json.loads(parsed)
        except Exception:
            meta = {}

    file_path = meta.get("path") if isinstance(meta, dict) else None

    # 1. Delete physical file / 删除物理文件
    file_deleted = False
    if file_path:
        try:
            file_deleted = storage.delete_file(file_path)
        except Exception as e:
            print(
                f"Warning: Failed to delete file "
                f"{file_path}: {e}"
            )

    # Also try by checksum as fallback / 也尝试通过校验和删除
    if not file_deleted:
        checksum = doc_data.get("checksum")
        if checksum:
            alt_path = storage.file_exists(checksum)
            if alt_path:
                try:
                    file_deleted = storage.delete_file(alt_path)
                except Exception as e:
                    print(
                        f"Warning: Failed to delete alt file "
                        f"{alt_path}: {e}"
                    )

    # 2+3. Delete document + orphan nodes / 删除文档和孤立节点
    delete_result = neo4j_client.delete_document(document_id)

    filename = doc_data.get("filename", "unknown")

    return {
        "success": True,
        "document_id": document_id,
        "filename": filename,
        "file_deleted": file_deleted,
        "edges_deleted": delete_result["edge_count"],
        "orphan_nodes_deleted": delete_result[
            "orphan_nodes_deleted"
        ],
    }


def _update_upload_status(
    job_id: str,
    status: str,
    progress: int,
    message: str,
    **kwargs,
):
    """
    Update job status for upload processing (supports Redis + fallback).
    更新上传处理任务的状态（支持 Redis 和内存回退）。

    Tries Redis RQ job first, then falls back to in-memory storage.

    Args:
        job_id:    Job ID / 任务 ID
        status:    Status string / 状态
        progress:  Percentage 0-100 / 进度百分比
        message:   Status message / 状态消息
        **kwargs:  Additional metadata (e.g., documentId, stats)
    """
    if queue.is_connected():
        try:
            from rq import get_current_job

            current_job = get_current_job()
            if current_job:
                meta = current_job.meta or {}
                meta.update(
                    {
                        "status": status,
                        "progress": progress,
                        "message": message,
                        **kwargs,
                    }
                )
                current_job.meta = meta
                current_job.save()
                return
        except Exception:
            pass

        try:
            job = queue.get_job(job_id)
            if job:
                meta = job.meta or {}
                meta.update(
                    {
                        "status": status,
                        "progress": progress,
                        "message": message,
                        **kwargs,
                    }
                )
                job.meta = meta
                job.save()
                return
        except Exception:
            pass

    # Fallback to in-memory / 回退到内存存储
    if job_id not in processing_jobs:
        processing_jobs[job_id] = {}
    processing_jobs[job_id].update(
        {
            "status": status,
            "progress": progress,
            "message": message,
            **kwargs,
        }
    )


def process_document_background(
    doc_id: str,
    file_path: str,
    kind: str,
    job_id: str,
    chunk_size: int = 2000,
    enable_ai_segmentation: bool = False,
    user_prompt: Optional[str] = None,
    optimize_prompt: bool = True,
    root_topic: Optional[str] = None,
):
    """
    Background task for processing a document into the knowledge graph.
    文档处理的后台任务：解析、抽取、链接并写入知识图谱。

    This function is designed to run as an RQ worker task or a FastAPI
    BackgroundTask. It handles the complete processing pipeline:

    Pipeline / 处理流水线::

        1. Parse document into chunks / 解析文档为文本块
        2a. AI mode: analyze structure → extract rich knowledge
        2b. Traditional mode: extract triplets from each chunk
        3. Link entities and merge aliases / 链接和合并实体
        4. Ingest into Neo4j graph / 写入图数据库

    Args:
        doc_id:                   Document ID / 文档 ID
        file_path:                Path to document file / 文档文件路径
        kind:                     Document type / 文档类型
        job_id:                   Job ID for progress tracking / 任务 ID
        chunk_size:               Max characters per chunk / 每块最大字符数
        enable_ai_segmentation:   Enable AI-powered extraction / 启用 AI 抽取
        user_prompt:              Custom analysis prompt / 自定义分析提示词
        optimize_prompt:          Optimize prompt via AI / 优化提示词
        root_topic:               Topic root node name / 主题根节点名称
    """
    _update_upload_status(
        job_id, "processing", 0, "开始处理文档...",
        documentId=doc_id,
    )

    try:
        print(f"\n{'#'*80}")
        print(f"🚀 [文档处理] 开始处理文档")
        print(f"   - 文档ID: {doc_id}")
        print(f"   - 文件路径: {file_path}")
        print(f"   - 文件类型: {kind}")
        print(f"   - 任务ID: {job_id}")
        print(f"   - Chunk大小: {chunk_size} 字符")
        print(
            f"   - AI智能分词: "
            f"{'启用' if enable_ai_segmentation else '禁用'}"
        )
        if user_prompt:
            print(
                f"   - 用户Prompt: {user_prompt[:100]}..."
            )
        print(f"{'#'*80}\n")

        # Step 1: Parse document / 第一步：解析文档
        _update_upload_status(
            job_id, "processing", 10, "正在解析文档...",
            documentId=doc_id,
        )

        print(
            f"📖 [步骤1] 解析文档 "
            f"(chunk_size={chunk_size})..."
        )
        parser = ParserFactory.create_parser(kind, chunk_size=chunk_size)
        full_text, chunks = parser.parse(file_path)
        print(
            f"✅ [步骤1] 解析完成: {len(chunks)} 个文本块，"
            f"总长度 {len(full_text)} 字符"
        )
        if chunks:
            avg_chunk_size = sum(len(c.text) for c in chunks) / len(
                chunks
            )
            print(
                f"   - 平均每个文本块: {avg_chunk_size:.0f} 字符"
            )

        # AI-powered segmentation mode / AI 智能分词模式
        if enable_ai_segmentation and ai_segmenter:
            print(f"\n🧠 [AI模式] 启用智能知识抽取")

            # Optimize user prompt if provided / 优化用户提示词
            final_prompt = None
            if user_prompt:
                _update_upload_status(
                    job_id, "processing", 15,
                    "正在优化分析提示词...",
                    documentId=doc_id,
                )

                if optimize_prompt:
                    print(
                        f"🔧 [Prompt优化] 优化用户提示词..."
                    )
                    final_prompt = (
                        ai_segmenter.optimize_user_prompt(
                            user_prompt
                        )
                    )
                else:
                    final_prompt = user_prompt
                    print(
                        f"📝 [Prompt] 使用原始用户提示词"
                    )

            # Analyze document structure / 分析文档结构
            _update_upload_status(
                job_id, "processing", 20,
                "正在分析文档结构...",
                documentId=doc_id,
            )

            print(
                f"\n🔍 [文档分析] 分析文档整体结构..."
            )
            doc_context = ai_segmenter.analyze_document_structure(
                chunks, final_prompt
            )
            print(f"✅ [文档分析] 完成:")
            print(
                f"   - 主题: "
                f"{', '.join(doc_context.get('themes', []))}"
            )
            print(
                f"   - 领域: "
                f"{', '.join(doc_context.get('domains', []))}"
            )
            print(
                f"   - 关键概念: "
                f"{', '.join(doc_context.get('key_concepts', [])[:5])}..."
            )

            # Extract rich knowledge from each chunk / 逐块提取丰富知识
            _update_upload_status(
                job_id, "processing", 30,
                "正在进行深度知识抽取...",
                documentId=doc_id,
            )

            print(
                f"\n💎 [深度抽取] 开始智能知识抽取 "
                f"(共 {len(chunks)} 个文本块)..."
            )
            all_triplets = []
            all_concepts = []
            all_insights = []

            for i, chunk in enumerate(chunks, 1):
                print(
                    f"\n📦 [文本块 {i}/{len(chunks)}] "
                    f"AI深度分析中..."
                )
                knowledge = ai_segmenter.extract_rich_knowledge(
                    chunk, doc_context, final_prompt
                )

                all_triplets.extend(
                    knowledge.get("triplets", [])
                )
                all_concepts.extend(
                    knowledge.get("concepts", [])
                )
                all_insights.extend(
                    knowledge.get("insights", [])
                )

                print(
                    f"   ✓ 提取: {len(knowledge.get('triplets', []))} "
                    f"个关系, {len(knowledge.get('concepts', []))} "
                    f"个概念, {len(knowledge.get('insights', []))} "
                    f"个洞察"
                )

                progress = 30 + int((i / len(chunks)) * 40)
                _update_upload_status(
                    job_id, "processing", progress,
                    f"AI深度分析中... ({i}/{len(chunks)})",
                    documentId=doc_id,
                )

            print(f"\n📊 [深度抽取] 完成:")
            print(f"   - 总关系数: {len(all_triplets)}")
            print(f"   - 总概念数: {len(all_concepts)}")
            print(f"   - 总洞察数: {len(all_insights)}")

            # Ingest rich concepts first / 先写入丰富概念
            _update_upload_status(
                job_id, "processing", 75,
                "正在构建丰富概念...",
                documentId=doc_id,
            )

            print(f"\n💎 [概念构建] 写入丰富概念信息...")
            graph_service.ingest_rich_concepts(
                doc_id, all_concepts, root_topic=root_topic
            )

            # Link and merge entities / 链接和合并实体
            _update_upload_status(
                job_id, "processing", 80,
                "正在链接实体...",
                documentId=doc_id,
            )

            print(f"\n🔗 [实体链接] 开始实体链接和合并...")
            linked_triplets = linker.link_and_merge(all_triplets)
            print(
                f"✅ [实体链接] 完成: "
                f"{len(linked_triplets)} 个三元组"
            )

            # Ingest triplets / 写入三元组
            _update_upload_status(
                job_id, "processing", 90,
                "正在构建知识图谱...",
                documentId=doc_id,
            )

            print(f"\n💾 [图谱构建] 开始构建知识图谱...")
            graph_service.ingest_triplets(
                doc_id, linked_triplets, root_topic=root_topic
            )
            print(f"✅ [图谱构建] 完成")

            concept_names = set(c["name"] for c in all_concepts)

            print(f"\n{'#'*80}")
            print(f"🎉 [AI智能处理] 处理完成!")
            print(f"   - 文本块数: {len(chunks)}")
            print(f"   - 丰富概念数: {len(all_concepts)}")
            print(f"   - 知识关系数: {len(linked_triplets)}")
            print(f"   - 深度洞察数: {len(all_insights)}")
            print(f"   - 文本总长度: {len(full_text)} 字符")
            if all_insights:
                print(f"\n💡 [关键洞察]:")
                for insight in all_insights[:3]:
                    print(f"   • {insight}")
            print(f"{'#'*80}\n")

            stats = {
                "chunks": len(chunks),
                "triplets": len(linked_triplets),
                "concepts": len(concept_names),
                "insights": len(all_insights),
                "textLength": len(full_text),
                "mode": "ai_segmentation",
            }
            result_data = {"stats": stats}
            if all_insights:
                result_data["insights"] = all_insights[:10]

            neo4j_client.mark_document_processed(
                doc_id, "completed"
            )

            _update_upload_status(
                job_id, "completed", 100,
                "AI智能分析完成！",
                documentId=doc_id, **result_data,
            )

        else:
            # Traditional extraction mode / 传统抽取模式
            _update_upload_status(
                job_id, "processing", 30,
                f"已提取 {len(chunks)} 个文本块，"
                f"正在进行知识抽取...",
                documentId=doc_id,
            )

            print(
                f"\n🤖 [步骤2] 开始知识抽取 "
                f"(共 {len(chunks)} 个文本块)..."
            )
            all_triplets = []
            chunk_triplet_counts = []

            for i, chunk in enumerate(chunks, 1):
                print(
                    f"\n📦 [文本块 {i}/{len(chunks)}] "
                    f"处理中..."
                )
                triplets = extractor.extract(chunk)
                all_triplets.extend(triplets)
                chunk_triplet_counts.append(len(triplets))
                progress = 30 + int((i / len(chunks)) * 40)
                _update_upload_status(
                    job_id, "processing", progress,
                    f"正在抽取知识... ({i}/{len(chunks)})",
                    documentId=doc_id,
                )

            print(f"\n📊 [步骤2] 知识抽取完成:")
            print(f"   - 总三元组数: {len(all_triplets)}")
            print(
                f"   - 各文本块三元组数: "
                f"{chunk_triplet_counts}"
            )
            print(
                f"   - 平均每个文本块: "
                f"{len(all_triplets) / len(chunks) if chunks else 0:.2f} "
                f"个三元组"
            )

            _update_upload_status(
                job_id, "processing", 70,
                f"已抽取 {len(all_triplets)} 个知识三元组，"
                f"正在链接实体...",
                documentId=doc_id,
            )

            # Link and merge entities / 链接和合并实体
            print(f"\n🔗 [步骤3] 开始实体链接和合并...")
            linked_triplets = linker.link_and_merge(all_triplets)
            print(
                f"✅ [步骤3] 实体链接完成: "
                f"{len(linked_triplets)} 个三元组"
            )

            _update_upload_status(
                job_id, "processing", 85,
                "正在构建知识图谱...",
                documentId=doc_id,
            )

            # Ingest into Neo4j / 写入 Neo4j
            print(f"\n💾 [步骤4] 开始构建知识图谱...")
            graph_service.ingest_triplets(
                doc_id, linked_triplets,
                root_topic=root_topic
            )
            print(f"✅ [步骤4] 知识图谱构建完成")

            concept_names = set(
                t.subject for t in linked_triplets
            ) | set(t.object for t in linked_triplets)

            print(f"\n{'#'*80}")
            print(f"🎉 [文档处理] 处理完成!")
            print(f"   - 文本块数: {len(chunks)}")
            print(f"   - 知识三元组数: {len(linked_triplets)}")
            print(f"   - 概念数量: {len(concept_names)}")
            print(f"   - 文本总长度: {len(full_text)} 字符")
            print(f"{'#'*80}\n")

            stats = {
                "chunks": len(chunks),
                "triplets": len(linked_triplets),
                "concepts": len(concept_names),
                "textLength": len(full_text),
                "mode": "traditional",
            }
            neo4j_client.mark_document_processed(
                doc_id, "completed"
            )
            _update_upload_status(
                job_id, "completed", 100,
                "知识图谱构建完成！",
                documentId=doc_id, stats=stats,
            )

    except Exception as e:
        print(f"\n{'#'*80}")
        print(f"❌ [文档处理] 处理失败!")
        print(f"   - 错误信息: {str(e)}")
        import traceback

        error_trace = traceback.format_exc()
        print(f"   - 错误详情:\n{error_trace}")
        print(f"{'#'*80}\n")

        _update_upload_status(
            job_id, "failed", 0,
            f"处理失败: {str(e)}",
            documentId=doc_id, error=error_trace,
        )


@router.post("/process", response_model=dict)
async def upload_and_process(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_process: bool = True,
    chunk_size: int = 2000,
    enable_ai_segmentation: bool = False,
    user_prompt: Optional[str] = None,
    optimize_prompt: bool = True,
    root_topic: Optional[str] = None,
):
    """
    Upload a file and automatically process it into the knowledge graph.
    一体化接口：上传文件并自动进行知识抽取和图谱构建。

    POST /uploads/process

    This is the main ingestion endpoint. It combines file upload and
    processing into a single operation with full configuration control.

    Args:
        file:                     Uploaded file / 上传的文件
        auto_process:             Auto-process after upload (default: True)
                                / 是否自动处理
        chunk_size:               Max characters per chunk (100-20000)
                                / 每块最大字符数
        enable_ai_segmentation:   Enable AI-powered extraction / 启用 AI 抽取
        user_prompt:              Custom analysis prompt / 自定义分析提示词
        optimize_prompt:          Optimize prompt via AI / 优化提示词
        root_topic:               Topic root node name / 主题根节点名称

    Returns:
        Dict with documentId, filename, status, and optional jobId
    """
    # Validate chunk_size / 验证分块大小
    if chunk_size < 100:
        raise HTTPException(
            status_code=400,
            detail="chunk_size 不能小于 100 字符",
        )
    if chunk_size > 20000:
        raise HTTPException(
            status_code=400,
            detail="chunk_size 不能大于 20000 字符"
            "（建议不超过 8000）",
        )

    # Validate AI segmentation / 验证 AI 分词
    if enable_ai_segmentation and not ai_segmenter:
        raise HTTPException(
            status_code=400,
            detail="AI智能分词需要配置 OPENAI_API_KEY "
            "环境变量",
        )

    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    kind = get_document_kind(file.filename)
    if kind == "unknown":
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unsupported file type: "
                f"{Path(file.filename).suffix or 'unknown'}. "
                f"Allowed types: {SUPPORTED_TYPES_LABEL}"
            ),
        )

    validate_content_type(file.content_type)

    # Save file / 保存文件
    file_path, checksum = await storage.save_file(
        content, file.filename
    )

    # Check duplicate / 检查重复
    existing_docs = neo4j_client.execute_query(
        "MATCH (d:Document {checksum: $checksum}) "
        "RETURN d.id as id LIMIT 1",
        {"checksum": checksum},
    )

    if existing_docs:
        return {
            "documentId": existing_docs[0]["id"],
            "filename": file.filename,
            "checksum": checksum,
            "status": "duplicate",
            "message": "文档已存在",
        }

    doc_id = f"doc_{uuid.uuid4().hex[:12]}"

    neo4j_client.create_document(
        doc_id=doc_id,
        filename=file.filename,
        checksum=checksum,
        kind=kind,
        size=len(content),
        mime=file.content_type,
        meta={"path": file_path},
    )

    response = {
        "documentId": doc_id,
        "filename": file.filename,
        "checksum": checksum,
        "status": "uploaded",
        "path": file_path,
    }

    # Start background processing if enabled / 如果启用，启动后台处理
    if auto_process and background_tasks:
        job_id = f"job_{uuid.uuid4().hex[:12]}"

        # Try Redis queue first / 优先使用 Redis 队列
        if queue.is_connected():
            job = queue.enqueue(
                process_document_background,
                doc_id,
                file_path,
                kind,
                job_id,
                chunk_size,
                enable_ai_segmentation,
                user_prompt,
                optimize_prompt,
                root_topic,
                job_timeout='1h',
            )

            if job:
                job.meta = {
                    "status": "queued",
                    "documentId": doc_id,
                    "progress": 0,
                    "message": "等待处理...",
                }
                job.save()
                response["status"] = "processing"
                response["jobId"] = job.id
                response["message"] = "文档已上传，正在后台处理..."
                return response

        # Fallback to BackgroundTasks / 回退到 BackgroundTasks
        _update_upload_status(
            job_id, "queued", 0, "等待处理...",
            documentId=doc_id,
        )

        background_tasks.add_task(
            process_document_background,
            doc_id,
            file_path,
            kind,
            job_id,
            chunk_size,
            enable_ai_segmentation,
            user_prompt,
            optimize_prompt,
            root_topic,
        )

        response["status"] = "processing"
        response["jobId"] = job_id
        response["message"] = "文档已上传，正在后台处理..."

    return response


@router.get("/status/{job_id}")
async def get_processing_status(job_id: str):
    """
    Get the status of a document processing job.
    获取文档处理任务的状态。

    GET /uploads/status/{job_id}

    Checks Redis RQ queue first, then falls back to in-memory storage.

    Args:
        job_id:  Job ID / 任务 ID

    Returns:
        Dict with status, documentId, progress, and message

    Raises:
        404: If job not found / 任务未找到
    """
    if queue.is_connected():
        status = queue.get_job_status(job_id)
        if status.get("status") != "not_found":
            return status

    if job_id not in processing_jobs:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return processing_jobs[job_id]


# Pydantic models for text and URL uploads


class TextUploadRequest(BaseModel):
    """
    Request model for uploading text content.
    文本内容上传的请求模型。

    Attributes:
        content:               Text content to process / 文本内容
        title:                 Optional document title / 可选文档标题
        auto_process:          Auto-process after upload / 是否自动处理
        chunk_size:            Max characters per chunk / 每块最大字符数
        enable_ai_segmentation: Enable AI-powered extraction / 启用 AI 抽取
        user_prompt:           Custom analysis prompt / 自定义分析提示词
        optimize_prompt:       Optimize prompt via AI / 优化提示词
        root_topic:            Topic root node name / 主题根节点名称
    """
    content: str
    title: Optional[str] = None
    auto_process: bool = True
    chunk_size: int = 2000
    enable_ai_segmentation: bool = False
    user_prompt: Optional[str] = None
    optimize_prompt: bool = True
    root_topic: Optional[str] = None


class URLUploadRequest(BaseModel):
    """
    Request model for uploading content from a URL.
    从 URL 抓取内容上传的请求模型。

    Attributes:
        url:                   Webpage URL / 网页链接
        title:                 Optional document title / 可选文档标题
        auto_process:          Auto-process after upload / 是否自动处理
        chunk_size:            Max characters per chunk / 每块最大字符数
        enable_ai_segmentation: Enable AI-powered extraction / 启用 AI 抽取
        user_prompt:           Custom analysis prompt / 自定义分析提示词
        optimize_prompt:       Optimize prompt via AI / 优化提示词
        root_topic:            Topic root node name / 主题根节点名称
    """
    url: str
    title: Optional[str] = None
    auto_process: bool = True
    chunk_size: int = 2000
    enable_ai_segmentation: bool = False
    user_prompt: Optional[str] = None
    optimize_prompt: bool = True
    root_topic: Optional[str] = None


@router.post("/text", response_model=dict)
async def upload_text(
    request: TextUploadRequest,
    background_tasks: BackgroundTasks,
):
    """
    Create a document from pasted text content.
    从粘贴的文本内容创建文档。

    POST /uploads/text

    Useful for quickly processing text snippets without creating a file.
    The text is saved as a .txt file in the uploads directory.

    Args:
        request:  Text content and processing options / 文本内容和处理选项
        background_tasks:  FastAPI background tasks / 后台任务

    Returns:
        Dict with documentId, filename, and status
    """
    chunk_size = request.chunk_size
    if chunk_size < 100:
        raise HTTPException(
            status_code=400,
            detail="chunk_size 不能小于 100 字符",
        )
    if chunk_size > 20000:
        raise HTTPException(
            status_code=400,
            detail="chunk_size 不能大于 20000 字符"
            "（建议不超过 8000）",
        )

    if request.enable_ai_segmentation and not ai_segmenter:
        raise HTTPException(
            status_code=400,
            detail="AI智能分词需要配置 OPENAI_API_KEY "
            "环境变量",
        )

    content = request.content.strip()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="文本内容不能为空",
        )

    title = (
        request.title
        or content[:30].replace('\n', ' ') + "..."
    )
    filename = f"{title}.txt"

    content_bytes = content.encode('utf-8')
    checksum = hashlib.sha256(content_bytes).hexdigest()

    # Check duplicate / 检查重复
    existing_docs = neo4j_client.execute_query(
        "MATCH (d:Document {checksum: $checksum}) "
        "RETURN d.id as id LIMIT 1",
        {"checksum": checksum},
    )

    if existing_docs:
        return {
            "documentId": existing_docs[0]["id"],
            "filename": filename,
            "checksum": checksum,
            "status": "duplicate",
            "message": "相同内容的文档已存在",
        }

    file_path, _ = await storage.save_file(
        content_bytes, filename
    )

    doc_id = f"doc_{uuid.uuid4().hex[:12]}"

    neo4j_client.create_document(
        doc_id=doc_id,
        filename=filename,
        checksum=checksum,
        kind="txt",
        size=len(content_bytes),
        mime="text/plain",
        meta={"path": file_path, "source": "text_input"},
    )

    response = {
        "documentId": doc_id,
        "filename": filename,
        "checksum": checksum,
        "status": "uploaded",
        "path": file_path,
    }

    if request.auto_process:
        job_id = f"job_{uuid.uuid4().hex[:12]}"

        if queue.is_connected():
            job = queue.enqueue(
                process_document_background,
                doc_id,
                file_path,
                "txt",
                job_id,
                chunk_size,
                request.enable_ai_segmentation,
                request.user_prompt,
                request.optimize_prompt,
                request.root_topic,
                job_timeout='1h',
            )

            if job:
                job.meta = {
                    "status": "queued",
                    "documentId": doc_id,
                    "progress": 0,
                    "message": "等待处理...",
                }
                job.save()
                response["status"] = "processing"
                response["jobId"] = job.id
                response["message"] = "文本已保存，正在后台处理..."
                return response

        _update_upload_status(
            job_id, "queued", 0, "等待处理...",
            documentId=doc_id,
        )

        background_tasks.add_task(
            process_document_background,
            doc_id,
            file_path,
            "txt",
            job_id,
            chunk_size,
            request.enable_ai_segmentation,
            request.user_prompt,
            request.optimize_prompt,
            request.root_topic,
        )

        response["status"] = "processing"
        response["jobId"] = job_id
        response["message"] = "文本已保存，正在后台处理..."

    return response


@router.post("/url", response_model=dict)
async def upload_url(
    request: URLUploadRequest,
    background_tasks: BackgroundTasks,
):
    """
    Scrape a webpage and create a document from its content.
    从网页 URL 抓取内容并创建文档。

    POST /uploads/url

    Fetches the webpage, extracts text content (stripping HTML, scripts,
    and styles), and creates a document for knowledge graph processing.

    Args:
        request:  URL and processing options / 网页链接和处理选项
        background_tasks:  FastAPI background tasks / 后台任务

    Returns:
        Dict with documentId, filename, status, and source URL
    """
    chunk_size = request.chunk_size
    if chunk_size < 100:
        raise HTTPException(
            status_code=400,
            detail="chunk_size 不能小于 100 字符",
        )
    if chunk_size > 20000:
        raise HTTPException(
            status_code=400,
            detail="chunk_size 不能大于 20000 字符"
            "（建议不超过 8000）",
        )

    if request.enable_ai_segmentation and not ai_segmenter:
        raise HTTPException(
            status_code=400,
            detail="AI智能分词需要配置 OPENAI_API_KEY "
            "环境变量",
        )

    import httpx
    from bs4 import BeautifulSoup

    url = request.url.strip()

    if not url:
        raise HTTPException(
            status_code=400,
            detail="URL 不能为空",
        )

    # Fetch webpage content / 获取网页内容
    try:
        async with httpx.AsyncClient(
            timeout=30.0, follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html_content = response.text
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=400,
            detail=f"无法访问该网页: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"抓取网页时出错: {str(e)}",
        )

    # Parse HTML and extract text / 解析 HTML 并提取文本
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements / 移除脚本和样式元素
        for script in soup(
            ["script", "style", "nav", "footer", "header"]
        ):
            script.decompose()

        page_title = (
            soup.title.string if soup.title else None
        )
        title = request.title or page_title or url

        text_content = soup.get_text(
            separator='\n', strip=True
        )

        lines = [
            line.strip()
            for line in text_content.split('\n')
            if line.strip()
        ]
        content = '\n'.join(lines)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"解析网页内容时出错: {str(e)}",
        )

    if not content or len(content) < 50:
        raise HTTPException(
            status_code=400,
            detail="网页内容过少或无法提取有效文本",
        )

    filename = f"{title[:50]}.txt"
    content_bytes = content.encode('utf-8')
    checksum = hashlib.sha256(content_bytes).hexdigest()

    # Check duplicate / 检查重复
    existing_docs = neo4j_client.execute_query(
        "MATCH (d:Document {checksum: $checksum}) "
        "RETURN d.id as id LIMIT 1",
        {"checksum": checksum},
    )

    if existing_docs:
        return {
            "documentId": existing_docs[0]["id"],
            "filename": filename,
            "checksum": checksum,
            "status": "duplicate",
            "message": "相同内容的文档已存在",
        }

    file_path, _ = await storage.save_file(
        content_bytes, filename
    )

    doc_id = f"doc_{uuid.uuid4().hex[:12]}"

    neo4j_client.create_document(
        doc_id=doc_id,
        filename=filename,
        checksum=checksum,
        kind="txt",
        size=len(content_bytes),
        mime="text/plain",
        meta={
            "path": file_path,
            "source": "url",
            "original_url": url,
        },
    )

    response = {
        "documentId": doc_id,
        "filename": filename,
        "checksum": checksum,
        "status": "uploaded",
        "path": file_path,
        "sourceUrl": url,
    }

    if request.auto_process:
        job_id = f"job_{uuid.uuid4().hex[:12]}"

        if queue.is_connected():
            job = queue.enqueue(
                process_document_background,
                doc_id,
                file_path,
                "txt",
                job_id,
                chunk_size,
                request.enable_ai_segmentation,
                request.user_prompt,
                request.optimize_prompt,
                request.root_topic,
                job_timeout='1h',
            )

            if job:
                job.meta = {
                    "status": "queued",
                    "documentId": doc_id,
                    "progress": 0,
                    "message": "等待处理...",
                }
                job.save()
                response["status"] = "processing"
                response["jobId"] = job.id
                response["message"] = (
                    "网页内容已抓取，正在后台处理..."
                )
                return response

        _update_upload_status(
            job_id, "queued", 0, "等待处理...",
            documentId=doc_id,
        )

        background_tasks.add_task(
            process_document_background,
            doc_id,
            file_path,
            "txt",
            job_id,
            chunk_size,
            request.enable_ai_segmentation,
            request.user_prompt,
            request.optimize_prompt,
            request.root_topic,
        )

        response["status"] = "processing"
        response["jobId"] = job_id
        response["message"] = (
            "网页内容已抓取，正在后台处理..."
        )

    return response
