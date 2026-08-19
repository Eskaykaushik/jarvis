import logging

import httpx

from app.config import settings
from app.providers.base import BaseProvider, ProviderResponse

logger = logging.getLogger(__name__)


class CerebrasProvider(BaseProvider):
    name = "cerebras"

    def __init__(self):
        self.api_url = "https://api.cerebras.ai/v1/chat/completions"
        self.api_key = settings.cerebras_api_key
        self.model = settings.cerebras_model or "llama-3.3-70b"

    async def generate(self, prompt: str, context: list[dict] | None = None) -> ProviderResponse:
        messages = []
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=settings.model_timeout) as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": settings.model_max_tokens,
                },
            )
            response.raise_for_status()

        data = response.json()
        text = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)

        logger.info("Cerebras response: %d tokens", tokens)

        return ProviderResponse(
            text=text,
            model=self.model,
            provider=self.name,
            tokens_used=tokens,
        )

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 5,
                    },
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning("Cerebras health check failed: %s", e)
            return False
