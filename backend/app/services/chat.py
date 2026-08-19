import logging
import time
import uuid

from app.cache.cache_key import make_cache_key
from app.cache.redis_cache import cache_get, cache_get_stale, cache_set
from app.config import settings
from app.models.schemas import ChatRequest, ChatResponse
from app.reliability.fallback_chain import FallbackChain

logger = logging.getLogger(__name__)

_system_prompt = "You are Jarvis, a helpful and concise AI assistant."


async def handle_chat(
    request: ChatRequest,
    chain: FallbackChain,
) -> ChatResponse:
    conversation_id = request.conversation_id or str(uuid.uuid4())
    context = await _load_conversation(conversation_id)
    context.append({"role": "user", "content": request.message})

    cache_key = make_cache_key("chat", request.message, context)

    cached = await cache_get(cache_key)
    if cached:
        logger.info("Cache hit for key %s", cache_key)
        return ChatResponse(
            response=cached["response"],
            conversation_id=conversation_id,
            model=cached.get("model", ""),
            provider=cached.get("provider", ""),
            cached=True,
        )

    stale = await cache_get_stale(cache_key)
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

    await cache_set(
        cache_key,
        result.text,
        ttl=settings.chat_cache_ttl,
        model=result.model,
        provider=result.provider,
    )

    context.append({"role": "assistant", "content": result.text})
    await _save_conversation(conversation_id, context)

    return ChatResponse(
        response=result.text,
        conversation_id=conversation_id,
        model=result.model,
        provider=result.provider,
    )


async def _load_conversation(conversation_id: str) -> list[dict]:
    from app.cache.redis_cache import cache_get as redis_get

    data = await redis_get(f"conv:{conversation_id}")
    if data and isinstance(data, dict):
        return data.get("messages", [])
    return []


async def _save_conversation(conversation_id: str, messages: list[dict]):
    from app.cache.redis_cache import get_redis

    r = await get_redis()
    import json
    payload = json.dumps({
        "messages": messages,
        "updated_at": time.time(),
    })
    await r.set(f"conv:{conversation_id}", payload, ex=86400 * 7)
