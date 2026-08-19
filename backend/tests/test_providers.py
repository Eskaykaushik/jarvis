import pytest
from unittest.mock import AsyncMock, MagicMock
from app.providers.base import BaseProvider, ProviderResponse
from app.reliability.fallback_chain import FallbackChain
from app.reliability.circuit_breaker import CircuitBreaker


class MockProvider(BaseProvider):
    def __init__(self, name, response=None, should_fail=False):
        self.name = name
        self._response = response or ProviderResponse(text="ok", model="mock", provider=name)
        self._should_fail = should_fail

    async def generate(self, prompt, context=None):
        if self._should_fail:
            raise RuntimeError(f"{self.name} failed")
        return self._response

    async def health_check(self):
        return not self._should_fail


@pytest.mark.asyncio
async def test_fallback_returns_first_success():
    p1 = MockProvider("groq")
    p2 = MockProvider("openrouter")
    chain = FallbackChain([p1, p2])
    result = await chain.generate("hello")
    assert result.text == "ok"
    assert result.provider == "groq"


@pytest.mark.asyncio
async def test_fallback_skips_failed_provider():
    p1 = MockProvider("groq", should_fail=True)
    p2 = MockProvider("openrouter", response=ProviderResponse(text="fallback", model="mock", provider="openrouter"))
    chain = FallbackChain([p1, p2])
    result = await chain.generate("hello")
    assert result.text == "fallback"
    assert result.provider == "openrouter"


@pytest.mark.asyncio
async def test_fallback_raises_when_all_fail():
    p1 = MockProvider("groq", should_fail=True)
    p2 = MockProvider("openrouter", should_fail=True)
    chain = FallbackChain([p1, p2])
    with pytest.raises(RuntimeError, match="All providers failed"):
        await chain.generate("hello")


@pytest.mark.asyncio
async def test_circuit_breaker_skips_open_provider():
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=60)
    p1 = MockProvider("groq", should_fail=True)
    p2 = MockProvider("openrouter", response=ProviderResponse(text="saved", model="mock", provider="openrouter"))
    chain = FallbackChain([p1, p2], cb)

    await chain.generate("hello")
    await chain.generate("hello")

    assert cb.is_open("groq") is True
    result = await chain.generate("hello")
    assert result.provider == "openrouter"


def test_health_status():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure("groq")
    p1 = MockProvider("groq")
    chain = FallbackChain([p1], cb)
    status = chain.health_status()
    assert status["groq"] == "degraded"
