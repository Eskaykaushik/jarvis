import json
import logging

from app.cache.cache_key import make_cache_key
from app.cache.redis_cache import (
    RedisUnavailableError,
    cache_get_safe,
    cache_set_safe,
    get_redis_safe,
)
from app.config import settings
from app.models.schemas import SummaryRequest, SummaryResponse
from app.reliability.fallback_chain import FallbackChain

logger = logging.getLogger(__name__)


async def handle_summary(
    request: SummaryRequest,
    chain: FallbackChain,
) -> SummaryResponse:
    r = await get_redis_safe()
    if r is None:
        raise RedisUnavailableError("Redis is unavailable; cannot load conversation")

    raw = await r.get(f"conv:{request.conversation_id}")
    if not raw:
        raise ValueError("Conversation not found")

    data = json.loads(raw)
    messages = data.get("messages", [])

    conversation_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages
    )

    prompt = request.custom_prompt or "Summarize the following conversation concisely:"
    full_prompt = f"{prompt}\n\n{conversation_text}"

    cache_key = make_cache_key("summary", full_prompt)
    cached = await cache_get_safe(cache_key)
    if cached:
        return SummaryResponse(
            summary=cached["response"],
            conversation_id=request.conversation_id,
            model=cached.get("model", ""),
            provider=cached.get("provider", ""),
        )

    result = await chain.generate(full_prompt)

    await cache_set_safe(
        cache_key,
        result.text,
        ttl=settings.summary_cache_ttl,
        model=result.model,
        provider=result.provider,
    )

    return SummaryResponse(
        summary=result.text,
        conversation_id=request.conversation_id,
        model=result.model,
        provider=result.provider,
    )
