import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat import handle_chat

router = APIRouter()
logger = logging.getLogger(__name__)

_chain = None


def set_chain(chain):
    global _chain
    _chain = chain


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        return await handle_chat(request, _chain)
    except RuntimeError as e:
        logger.error("Chat failed: %s", e)
        raise HTTPException(status_code=503, detail="All providers failed. Please try again.")
    except Exception as e:
        logger.exception("Unexpected chat error")
        raise HTTPException(status_code=500, detail="An unexpected error occurred. Please try again.")
