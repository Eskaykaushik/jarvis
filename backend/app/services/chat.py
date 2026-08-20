import logging
import time
import uuid

from app.cache.cache_key import make_cache_key
from app.cache.redis_cache import (
    cache_get_safe,
    cache_get_stale_safe,
    cache_set_safe,
    get_redis_safe,
)
from app.config import settings
from app.models.schemas import ChatRequest, ChatResponse
from app.reliability.fallback_chain import FallbackChain

logger = logging.getLogger(__name__)

_system_prompt = "You are Kaushix, a helpful and concise AI assistant."


async def handle_chat(
    request: ChatRequest,
    chain: FallbackChain,
    user_id: str | None = None,
) -> ChatResponse:
    conversation_id = request.conversation_id or str(uuid.uuid4())
    context = await _load_conversation(user_id, conversation_id)
    context.append({"role": "user", "content": request.message})

    cache_key = make_cache_key("chat", request.message, context)

    cached = await cache_get_safe(cache_key)
    if cached:
        logger.info("Cache hit for key %s", cache_key)
        return ChatResponse(
            response=cached["response"],
            conversation_id=conversation_id,
            model=cached.get("model", ""),
            provider=cached.get("provider", ""),
            cached=True,
        )

    stale = await cache_get_stale_safe(cache_key)
    if stale:
        logger.info("Stale hit for key %s", cache_key)
        _ = chain.generate(
            request.message,
            [{"role": "system", "content": _system_prompt}] + context[:-1],
        )
        return ChatResponse(
            response=stale["response"],
            conversation_id=conversation_id,
            model=stale.get("model", ""),
            provider=stale.get("provider", ""),
            cached=True,
        )

    messages = [{"role": "system", "content": _system_prompt}] + context
    result = await chain.generate(request.message, messages)

    await cache_set_safe(
        cache_key,
        result.text,
        ttl=settings.chat_cache_ttl,
        model=result.model,
        provider=result.provider,
    )

    context.append({"role": "assistant", "content": result.text})
    await _save_conversation(user_id, conversation_id, context)

    return ChatResponse(
        response=result.text,
        conversation_id=conversation_id,
        model=result.model,
        provider=result.provider,
    )


def _conv_key(user_id: str | None, conversation_id: str) -> str:
    prefix = f"conv:{user_id}:" if user_id else "conv:"
    return f"{prefix}{conversation_id}"


async def _load_conversation(user_id: str | None, conversation_id: str) -> list[dict]:
    data = await cache_get_safe(_conv_key(user_id, conversation_id))
    if data and isinstance(data, dict):
        return data.get("messages", [])
    return []


async def _save_conversation(user_id: str | None, conversation_id: str, messages: list[dict]):
    r = await get_redis_safe()
    if r is None:
        logger.warning("Redis unavailable; conversation %s not persisted", conversation_id)
        return
    import json
    payload = json.dumps({
        "messages": messages,
        "updated_at": time.time(),
    })
    await r.set(_conv_key(user_id, conversation_id), payload, ex=86400 * 7)