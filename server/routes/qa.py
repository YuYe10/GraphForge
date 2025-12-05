"""Q&A API routes for intelligent question answering."""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from services.qa_service import qa_service


# Request/Response models
class Message(BaseModel):
    """A single message in conversation history."""
    role: str  # "user" or "assistant"
    content: str


class AskRequest(BaseModel):
    """Request model for asking a question."""
    question: str
    conversation_history: Optional[List[Message]] = None
    use_kg: bool = True  # Use knowledge graph context


class AskResponse(BaseModel):
    """Response model for Q&A endpoint."""
    success: bool
    answer: str
    used_context: bool
    context_snippet: Optional[str] = None
    error: Optional[str] = None


# Create router
router = APIRouter(prefix="/qa", tags=["Q&A"])


@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest) -> AskResponse:
    """
    Ask a question to the AI using knowledge graph context.
    
    Args:
        request: Question and optional conversation history
        
    Returns:
        Answer with metadata about context usage
    """
    try:
        # Validate input
        if not request.question or not request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )
        
        # Convert Message objects to dicts
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]
        
        # Get answer from QA service
        result = qa_service.answer_question(
            question=request.question,
            conversation_history=history,
            use_kg=request.use_kg
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to answer question")
            )
        
        return AskResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [API] 问答请求失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Check if Q&A service is available."""
    return {
        "status": "healthy" if qa_service.ai_client else "unhealthy",
        "provider": qa_service.settings.ai_provider,
        "has_ai_client": qa_service.ai_client is not None
    }
