"""
Document Ingestion API Routes
==============================

文档处理流水线 API 路由，提供文档解析、知识抽取、实体链接和图谱写入。

Provides the document ingestion pipeline — the core processing workflow that
transforms uploaded documents into knowledge graph entities. The pipeline
supports both traditional triplet extraction and AI-powered rich knowledge
extraction.

Pipeline stages / 处理流水线::

    1. Parse document into chunks / 解析文档为文本块
    2. Extract triplets or rich knowledge / 抽取三元组或丰富知识
    3. Link entities to existing concepts / 链接实体到已有概念
    4. Ingest into Neo4j graph / 写入 Neo4j 图数据库

Endpoints / 接口列表::

    POST   /ingest/{document_id}    Trigger ingestion / 触发文档处理
    GET    /ingest/status/{job_id}   Get job status / 获取处理状态
    DELETE /ingest/cancel/{job_id}   Cancel a job / 取消处理任务

Features / 主要特性::
    - Redis-backed task queue with fallback to BackgroundTasks
      / Redis 任务队列，fallback 到 BackgroundTasks
    - Real-time progress tracking / 实时进度跟踪
    - Job cancellation support (graceful shutdown)
      / 任务取消支持（优雅关闭）
    - Traditional and AI-powered extraction modes
      / 传统模式和 AI 驱动模式
"""
import json
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Optional
from pathlib import Path
from infra.neo4j_client import neo4j_client
from infra.storage import Storage
from services.parser import ParserFactory
from services.extractor import TripletExtractor
from services.linker import EntityLinker
from services.graph_service import GraphService
from services.ai_segmenter import AISegmenter
from infra.queue import get_queue, update_job_progress

router = APIRouter(prefix="/ingest", tags=["ingest"])

storage = Storage()
extractor = TripletExtractor()
linker = EntityLinker()
graph_service = GraphService()

# Initialize AI segmenter (optional — requires AI provider config)
# 初始化 AI 分词器（可选——需要 AI 提供商配置）
try:
    ai_segmenter = AISegmenter()
except ValueError:
    ai_segmenter = None

# Initialize Redis queue / 初始化 Redis 队列
queue = get_queue()

# Fallback job storage (used when Redis is unavailable)
# 备用的内存任务存储（Redis 不可用时使用）
jobs: Dict[str, Dict] = {}


def _is_job_cancelled(job_id: str) -> bool:
    """
    Check if a job has been cancelled by the user.
    检查任务是否已被用户取消。

    Checks both Redis (via RQ meta._cancelled flag) and in-memory fallback.
    This is called periodically during processing to support graceful shutdown.

    Args:
        job_id:  Job ID to check / 要检查的任务 ID

    Returns:
        True if the job has been cancelled / 已取消则返回 True
    """
    if queue.is_connected():
        try:
            from rq import get_current_job

            current_job = get_current_job()
            if current_job:
                meta = current_job.meta or {}
                return meta.get('_cancelled', False)
        except Exception:
            pass

        try:
            job = queue.get_job(job_id)
            if job:
                meta = job.meta or {}
                return meta.get('_cancelled', False)
        except Exception:
            pass

    # Fallback to in-memory / 回退到内存存储
    if job_id in jobs:
        return jobs[job_id].get("status") == "cancelled"

    return False


def _update_status(
    job_id: str,
    status: str,
    progress: int,
    message: str,
    **kwargs,
):
    """
    Update job status with support for both Redis and fallback storage.
    更新任务状态，支持 Redis 和内存两种存储方式。

    Args:
        job_id:    Job ID / 任务 ID
        status:    Status string / 状态字符串
        progress:  Progress percentage (0-100) / 进度百分比
        message:   Status message / 状态消息
        **kwargs:  Additional metadata / 附加元数据
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

    # Fallback to in-memory storage / 回退到内存存储
    if job_id not in jobs:
        jobs[job_id] = {}
    jobs[job_id].update(
        {
            "status": status,
            "progress": progress,
            "message": message,
            **kwargs,
        }
    )


def process_document(
    doc_id: str,
    file_path: str,
    kind: str,
    job_id: str,
    chunk_size: int = 2000,
    enable_ai_segmentation: bool = False,
    user_prompt: Optional[str] = None,
    optimize_prompt: bool = True,
):
    """
    Process a document through the full ingestion pipeline.
    通过完整处理流水线处理文档。

    This is the core background task that executes the knowledge extraction
    pipeline. It is designed to be run via RQ or FastAPI BackgroundTasks.

    Pipeline / 流水线::

        1. Parse document using file-type-specific parser
        2. If AI mode: analyze structure → extract rich knowledge
        3. If traditional mode: extract triplets from each chunk
        4. Link entities and merge aliases
        5. Ingest linked triplets into Neo4j

    Args:
        doc_id:                   Document ID / 文档 ID
        file_path:                Path to the document file / 文档文件路径
        kind:                     Document type / 文档类型
        job_id:                   Job ID for progress tracking / 任务 ID
        chunk_size:               Max characters per chunk / 每块最大字符数
        enable_ai_segmentation:   Enable AI-powered analysis / 启用 AI 分析
        user_prompt:              Custom analysis prompt / 自定义分析提示词
        optimize_prompt:          Optimize prompt via AI / 优化提示词
    """
    _update_status(
        job_id, "processing", 0, "Starting parsing...",
        documentId=doc_id
    )

    try:
        # Check cancellation before starting / 开始前检查取消
        if _is_job_cancelled(job_id):
            return

        # Step 1: Parse document / 第一步：解析文档
        _update_status(
            job_id, "processing", 10, "Parsing document...",
            documentId=doc_id
        )

        parser = ParserFactory.create_parser(kind, chunk_size=chunk_size)
        full_text, chunks = parser.parse(file_path)

        if _is_job_cancelled(job_id):
            return

        # AI-powered segmentation mode / AI 智能分词模式
        if enable_ai_segmentation and ai_segmenter:
            final_prompt = None
            if user_prompt:
                _update_status(
                    job_id, "processing", 15,
                    "Optimizing prompt...", documentId=doc_id
                )

                if _is_job_cancelled(job_id):
                    return

                if optimize_prompt:
                    final_prompt = ai_segmenter.optimize_user_prompt(
                        user_prompt
                    )
                else:
                    final_prompt = user_prompt

            if _is_job_cancelled(job_id):
                return

            # Analyze document structure / 分析文档结构
            _update_status(
                job_id, "processing", 20,
                "Analyzing document structure...",
                documentId=doc_id,
            )

            doc_context = ai_segmenter.analyze_document_structure(
                chunks, final_prompt
            )

            if _is_job_cancelled(job_id):
                return

            # Extract rich knowledge from each chunk / 逐块提取丰富知识
            _update_status(
                job_id, "processing", 30,
                "Extracting rich knowledge...",
                documentId=doc_id,
            )

            all_triplets = []
            all_concepts = []
            all_insights = []

            for i, chunk in enumerate(chunks, 1):
                if _is_job_cancelled(job_id):
                    return

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

                progress = 30 + int((i / len(chunks)) * 40)
                _update_status(
                    job_id, "processing", progress,
                    f"AI analyzing... ({i}/{len(chunks)})",
                    documentId=doc_id,
                )

            # Ingest rich concepts first / 先写入丰富概念
            _update_status(
                job_id, "processing", 75,
                "Ingesting rich concepts...",
                documentId=doc_id,
            )

            graph_service.ingest_rich_concepts(doc_id, all_concepts)

            # Link and merge entities / 链接和合并实体
            _update_status(
                job_id, "processing", 80,
                "Linking entities...",
                documentId=doc_id,
            )

            linked_triplets = linker.link_and_merge(all_triplets)

            # Ingest triplets / 写入三元组
            _update_status(
                job_id, "processing", 90,
                "Ingesting into graph...",
                documentId=doc_id,
            )

            graph_service.ingest_triplets(doc_id, linked_triplets)

            concept_names = set(c["name"] for c in all_concepts)

            stats = {
                "chunks": len(chunks),
                "triplets": len(linked_triplets),
                "concepts": len(concept_names),
                "insights": len(all_insights),
                "mode": "ai_segmentation",
            }

            result_data = {"stats": stats}
            if all_insights:
                result_data["insights"] = all_insights[:10]

            _update_status(
                job_id, "completed", 100,
                "AI analysis completed!",
                documentId=doc_id, **result_data,
            )

        else:
            # Traditional extraction mode / 传统抽取模式
            _update_status(
                job_id, "processing", 30,
                f"Extracted {len(chunks)} chunks. "
                f"Extracting triplets...",
                documentId=doc_id,
            )

            all_triplets = []
            for i, chunk in enumerate(chunks):
                if _is_job_cancelled(job_id):
                    return

                triplets = extractor.extract(chunk)
                all_triplets.extend(triplets)
                progress = 30 + int((i + 1) / len(chunks) * 40)
                _update_status(
                    job_id, "processing", progress,
                    f"Extracting triplets... "
                    f"({i + 1}/{len(chunks)})",
                    documentId=doc_id,
                )

            if _is_job_cancelled(job_id):
                return

            _update_status(
                job_id, "processing", 70,
                f"Extracted {len(all_triplets)} triplets. "
                f"Linking entities...",
                documentId=doc_id,
            )

            linked_triplets = linker.link_and_merge(all_triplets)

            if _is_job_cancelled(job_id):
                return

            _update_status(
                job_id, "processing", 90,
                "Ingesting into graph...",
                documentId=doc_id,
            )

            graph_service.ingest_triplets(doc_id, linked_triplets)

            stats = {
                "chunks": len(chunks),
                "triplets": len(linked_triplets),
                "concepts": len(
                    set(t.subject for t in linked_triplets)
                    | set(t.object for t in linked_triplets)
                ),
                "mode": "traditional",
            }

            _update_status(
                job_id, "completed", 100,
                f"Successfully processed "
                f"{len(linked_triplets)} triplets",
                documentId=doc_id, stats=stats,
            )

    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        _update_status(
            job_id, "failed", 0, f"Error: {str(e)}",
            documentId=doc_id, error=error_trace,
        )


@router.post("/{document_id}")
async def ingest_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    chunk_size: int = 2000,
    enable_ai_segmentation: bool = False,
    user_prompt: Optional[str] = None,
    optimize_prompt: bool = True,
):
    """
    Trigger ingestion processing for a document.
    触发文档的处理流水线。

    POST /ingest/{document_id}

    Validates the document exists, then starts background processing.
    The document goes through: parse → extract → link → ingest.

    Args:
        document_id:             Document ID to process / 待处理的文档 ID
        chunk_size:              Max characters per chunk (100-20000)
                                / 每块最大字符数
        enable_ai_segmentation:  Enable AI-powered extraction / 启用 AI 抽取
        user_prompt:             Custom analysis prompt / 自定义分析提示词
        optimize_prompt:         Optimize prompt via AI / 优化提示词

    Returns:
        Dict with jobId, documentId, and status
        包含任务 ID、文档 ID 和状态的字典

    Raises:
        400: Invalid parameters, missing AI config
        404: Document or file not found
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

    # Validate AI segmentation / 验证 AI 分词配置
    if enable_ai_segmentation and not ai_segmenter:
        raise HTTPException(
            status_code=400,
            detail="AI智能分词需要配置 OPENAI_API_KEY 环境变量",
        )

    # Get document info / 获取文档信息
    result = neo4j_client.execute_query(
        """
        MATCH (d:Document {id: $doc_id})
        RETURN d.filename as filename, d.kind as kind, d.meta as meta
        """,
        {"doc_id": document_id},
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    doc_data = result[0]
    filename = doc_data["filename"]
    kind = doc_data["kind"]

    # Parse meta JSON string if present / 解析元数据 JSON
    meta = {}
    if doc_data.get("meta"):
        try:
            meta = (
                json.loads(doc_data["meta"])
                if isinstance(doc_data["meta"], str)
                else doc_data["meta"]
            )
        except (json.JSONDecodeError, TypeError):
            meta = {}

    file_path = meta.get("path") or storage.get_file_path(filename)

    if not Path(file_path).exists():
        raise HTTPException(
            status_code=404,
            detail="File not found on disk",
        )

    # Create job ID / 创建任务 ID
    job_id = f"job_{uuid.uuid4().hex[:12]}"

    # Try Redis queue first / 优先使用 Redis 队列
    if queue.is_connected():
        job = queue.enqueue(
            process_document,
            document_id,
            str(file_path),
            kind,
            job_id,
            chunk_size,
            enable_ai_segmentation,
            user_prompt,
            optimize_prompt,
            job_timeout='1h',
        )

        if job:
            job.meta = {
                "status": "queued",
                "documentId": document_id,
                "progress": 0,
                "message": "Queued for processing",
            }
            job.save()
            return {
                "jobId": job.id,
                "documentId": document_id,
                "status": "queued",
            }

    # Fallback to BackgroundTasks / 回退到 BackgroundTasks
    _update_status(
        job_id, "queued", 0, "Queued for processing",
        documentId=document_id,
    )

    background_tasks.add_task(
        process_document,
        document_id,
        str(file_path),
        kind,
        job_id,
        chunk_size,
        enable_ai_segmentation,
        user_prompt,
        optimize_prompt,
    )

    return {
        "jobId": job_id,
        "documentId": document_id,
        "status": "queued",
    }


@router.get("/status/{job_id}")
async def get_ingest_status(job_id: str):
    """
    Get the status of an ingestion job.
    获取文档处理任务的状态。

    GET /ingest/status/{job_id}

    Checks Redis first, then falls back to in-memory storage.

    Args:
        job_id:  Job ID / 任务 ID

    Returns:
        Dict with status, progress, message, and documentId
        包含状态、进度、消息和文档 ID 的字典

    Raises:
        404: If job not found / 任务未找到
    """
    if queue.is_connected():
        status = queue.get_job_status(job_id)
        if status.get("status") != "not_found":
            return status

    if job_id not in jobs:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return jobs[job_id]


@router.delete("/cancel/{job_id}")
async def cancel_ingest_job(job_id: str):
    """
    Cancel a running or queued ingestion job.
    取消正在运行或排队的处理任务。

    DELETE /ingest/cancel/{job_id}

    For running jobs, sets a cancellation flag that the worker process
    checks before processing each chunk, enabling graceful shutdown.

    Args:
        job_id:  Job ID to cancel / 要取消的任务 ID

    Returns:
        Dict with success message / 包含成功消息的字典

    Raises:
        400: If job cannot be cancelled (already completed/failed)
    """
    if queue.is_connected():
        success = queue.cancel_job(job_id)
        if success:
            if job_id in jobs:
                jobs[job_id].update({
                    "status": "cancelled",
                    "message": "任务已被用户取消",
                })
            return {
                "message": "Job cancelled successfully",
                "jobId": job_id,
            }
        else:
            status = queue.get_job_status(job_id)
            if status.get("status") == "not_found":
                jobs[job_id] = {
                    "status": "cancelled",
                    "message": "任务已被用户取消",
                    "progress": 0,
                }
                return {
                    "message": "Job cancelled successfully",
                    "jobId": job_id,
                }
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Job cannot be cancelled "
                           "(already completed or failed)",
                )

    # Fallback: in-memory / 回退到内存存储
    if job_id not in jobs:
        jobs[job_id] = {
            "status": "cancelled",
            "message": "任务已被用户取消",
            "progress": 0,
        }
        return {
            "message": "Job cancelled successfully",
            "jobId": job_id,
        }

    current_status = jobs[job_id].get("status")
    if current_status in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Job cannot be cancelled (status: {current_status})",
        )

    jobs[job_id].update({
        "status": "cancelled",
        "message": "任务已被用户取消",
    })

    return {
        "message": "Job cancelled successfully",
        "jobId": job_id,
    }
