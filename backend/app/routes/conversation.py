import json
import logging

from fastapi import APIRouter, HTTPException

from app.auth.deps import AuthenticatedUser
from app.cache.redis_cache import get_redis_safe
from app.models.schemas import Conversation, ConversationSummary

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(user_id: AuthenticatedUser):
    r = await get_redis_safe()
    if r is None:
        raise HTTPException(
            status_code=503,
            detail="Cache service is unavailable. Please try again later.",
        )

    prefix = f"conv:{user_id}:"
    conversations = []
    async for key in r.scan_iter(match=f"{prefix}*"):
        raw = await r.get(key)
        if not raw:
            continue
        data = json.loads(raw)
        conv_id = key.removeprefix(prefix)
        messages = data.get("messages", [])
        title = _extract_title(messages)
        conversations.append(ConversationSummary(
            id=conv_id,
            title=title,
            updated_at=data.get("updated_at", 0),
        ))

    conversations.sort(key=lambda c: c.updated_at, reverse=True)
    return conversations


@router.get("/conversation/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str, user_id: AuthenticatedUser):
    r = await get_redis_safe()
    if r is None:
        raise HTTPException(
            status_code=503,
            detail="Cache service is unavailable. Please try again later.",
        )

    raw = await r.get(f"conv:{user_id}:{conversation_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Conversation not found")

    data = json.loads(raw)
    return Conversation(
        id=conversation_id,
        messages=data.get("messages", []),
        created_at=data.get("created_at", 0),
        updated_at=data.get("updated_at", 0),
    )


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str, user_id: AuthenticatedUser):
    r = await get_redis_safe()
    if r is None:
        raise HTTPException(
            status_code=503,
            detail="Cache service is unavailable. Please try again later.",
        )

    key = f"conv:{user_id}:{conversation_id}"
    deleted = await r.delete(key)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"deleted": True, "id": conversation_id}


def _extract_title(messages: list[dict]) -> str:
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            return content[:80] + ("..." if len(content) > 80 else "")
    return "New conversation"
