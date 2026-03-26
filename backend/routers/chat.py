import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.deps import get_db, get_current_user
from backend.models.user import User
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Process a chat message using AI with tool-use to drive Home Hub actions."""
    if not settings.anthropic_api_key or settings.anthropic_api_key.startswith("your-"):
        raise HTTPException(
            status_code=503,
            detail="Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env",
        )

    try:
        service = ChatService(db, user)
        result = await service.chat(data.message)
        return ChatResponse(
            response=result["response"],
            actions_taken=result["actions_taken"],
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat service error: {str(e)}")
