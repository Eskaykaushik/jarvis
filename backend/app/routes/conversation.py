import json
import time
import logging

from fastapi import APIRouter, HTTPException

from app.cache.redis_cache import get_redis_safe
from app.models.schemas import Conversation

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/conversation/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    r = await get_redis_safe()
    if r is None:
        raise HTTPException(
            status_code=503,
            detail="Cache service is unavailable. Please try again later.",
        )

    raw = await r.get(f"conv:{conversation_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Conversation not found")

    data = json.loads(raw)
    return Conversation(
        id=conversation_id,
        messages=data.get("messages", []),
        created_at=data.get("created_at", 0),
        updated_at=data.get("updated_at", 0),
    )
