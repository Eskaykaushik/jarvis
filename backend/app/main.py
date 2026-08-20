import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.providers.groq_provider import GroqProvider
from app.providers.openrouter_provider import OpenRouterProvider
from app.providers.together_provider import TogetherProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.cerebras_provider import CerebrasProvider
from app.reliability.circuit_breaker import CircuitBreaker
from app.reliability.fallback_chain import FallbackChain
from app.routes.chat import router as chat_router, set_chain as set_chat_chain
from app.routes.summary import router as summary_router, set_chain as set_summary_chain
from app.routes.email import router as email_router
from app.routes.conversation import router as conversation_router
from app.cache.redis_cache import close_redis, cache_health

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.app_name,
    description="AI Assistant Service with multi-provider fallback",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://eskaykaushik.github.io",
        "http://localhost:8080",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

providers = []
if settings.groq_api_key:
    providers.append(GroqProvider())
if settings.openrouter_api_key:
    providers.append(OpenRouterProvider())
if settings.together_api_key:
    providers.append(TogetherProvider())
if settings.gemini_api_key:
    providers.append(GeminiProvider())
if settings.cerebras_api_key:
    providers.append(CerebrasProvider())

cb = CircuitBreaker()
chain = FallbackChain(providers, cb)
set_chat_chain(chain)
set_summary_chain(chain)

app.include_router(chat_router)
app.include_router(summary_router)
app.include_router(email_router)
app.include_router(conversation_router)


@app.get("/health")
async def health():
    redis_ok = await cache_health()
    provider_status = chain.health_status()
    return {
        "status": "ok" if redis_ok else "degraded",
        "service": settings.app_name,
        "providers": provider_status or {p.name: "unknown" for p in providers},
        "redis": "connected" if redis_ok else "disconnected",
    }


@app.on_event("shutdown")
async def shutdown():
    await close_redis()
