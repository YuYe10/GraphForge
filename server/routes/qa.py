"""
Q&A API Routes — Intelligent Question Answering
=================================================

智能问答 API 路由，基于知识图谱和 AI 提供问答能力。

Provides RESTful endpoints for asking questions with knowledge graph context.
The QA service retrieves relevant entities from Neo4j and uses AI to
generate contextualized answers.

Endpoints / 接口列表::

    POST /qa/ask     Ask a question / 提问
    GET  /qa/health  Check QA service health / 健康检查
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from services.qa_service import qa_service


# Request/Response models / 请求/响应模型


class Message(BaseModel):
    """
    A single message in a conversation history.
    对话历史中的一条消息。

    Attributes:
        role:     Message role: "user" or "assistant" / 角色
        content:  Message text content / 消息文本内容
    """
    role: str
    content: str


class AskRequest(BaseModel):
    """
    Request model for asking a question.
    提问请求模型。

    Attributes:
        question:             User's question text / 用户问题文本
        conversation_history: Previous messages for context
                            / 用于上下文的之前消息
        use_kg:               Whether to use knowledge graph context
                            / 是否使用知识图谱上下文
    """
    question: str
    conversation_history: Optional[List[Message]] = None
    use_kg: bool = True


class AskResponse(BaseModel):
    """
    Response model for the Q&A endpoint.
    问答端点的响应模型。

    Attributes:
        success:          Whether the answer was generated successfully
                        / 是否成功生成答案
        answer:           Generated answer text / 生成的答案文本
        used_context:     Whether knowledge graph context was used
                        / 是否使用了知识图谱上下文
        context_snippet:  Preview of the KG context (first 300 chars)
                        / 知识图谱上下文预览（前 300 字符）
        error:            Error message if failed / 失败时的错误消息
    """
    success: bool
    answer: str
    used_context: bool
    context_snippet: Optional[str] = None
    error: Optional[str] = None


router = APIRouter(prefix="/qa", tags=["Q&A"])


@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest) -> AskResponse:
    """
    Ask a question to the AI using knowledge graph context.
    使用知识图谱上下文向 AI 提问。

    POST /qa/ask

    The endpoint:
    1. Validates the input question / 验证输入问题
    2. Optionally retrieves relevant entities from the knowledge graph
       / 可选地从知识图谱检索相关实体
    3. Sends the question + context to the AI / 发送问题和上下文给 AI
    4. Returns the generated answer / 返回生成的答案

    Args:
        request:  Question and configuration / 问题及配置

    Returns:
        AskResponse with answer and metadata / 包含答案和元数据的响应

    Raises:
        400: If question is empty / 如果问题为空
        500: If AI service fails / 如果 AI 服务失败
    """
    try:
        # Validate input / 验证输入
        if not request.question or not request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty",
            )

        # Convert Message objects to dicts / 转换 Message 对象为字典
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]

        # Get answer from QA service / 从 QA 服务获取答案
        result = qa_service.answer_question(
            question=request.question,
            conversation_history=history,
            use_kg=request.use_kg,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to answer question"),
            )

        return AskResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [API] 问答请求失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/health")
async def health_check():
    """
    Check if the Q&A service is available and healthy.
    检查问答服务是否可用和健康。

    GET /qa/health

    Reports:
    - Status: healthy/unhealthy based on AI client availability
    - Provider: Current AI provider name
    - has_ai_client: Whether the AI client is initialized

    Returns:
        Dict with health status and provider info
        包含健康状态和提供商信息的字典
    """
    return {
        "status": (
            "healthy" if qa_service.ai_client else "unhealthy"
        ),
        "provider": qa_service.settings.ai_provider,
        "has_ai_client": qa_service.ai_client is not None,
    }
