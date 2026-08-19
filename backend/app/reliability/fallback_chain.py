import logging

from app.providers.base import BaseProvider, ProviderResponse
from app.reliability.circuit_breaker import CircuitBreaker
from app.reliability.retry import with_retry

logger = logging.getLogger(__name__)


class FallbackChain:
    def __init__(self, providers: list[BaseProvider], circuit_breaker: CircuitBreaker | None = None):
        self.providers = providers
        self.cb = circuit_breaker or CircuitBreaker()

    async def generate(self, prompt: str, context: list[dict] | None = None) -> ProviderResponse:
        for provider in self.providers:
            if self.cb.is_open(provider.name):
                logger.info("Skipping %s (circuit open)", provider.name)
                continue

            try:
                response = await self._call_provider(provider, prompt, context)
                self.cb.record_success(provider.name)
                return response
            except Exception as e:
                logger.warning("Provider %s failed: %s", provider.name, e)
                self.cb.record_failure(provider.name)

        raise RuntimeError("All providers failed")

    @with_retry(max_retries=2, base_delay=1.0)
    async def _call_provider(
        self, provider: BaseProvider, prompt: str, context: list[dict] | None
    ) -> ProviderResponse:
        return await provider.generate(prompt, context)

    def health_status(self) -> dict[str, str]:
        return self.cb.status()
