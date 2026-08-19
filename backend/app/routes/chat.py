from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat import handle_chat

router = APIRouter()

_chain = None


def set_chain(chain):
    global _chain
    _chain = chain


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return await handle_chat(request, _chain)
