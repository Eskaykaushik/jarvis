import logging
import re

from groq import AsyncGroq

from app.config import settings
from app.providers.base import BaseProvider, ProviderResponse

logger = logging.getLogger(__name__)


def _strip_thinking(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return cleaned.strip()


class GroqProvider(BaseProvider):
    name = "groq"

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = settings.groq_model

    async def generate(self, prompt: str, context: list[dict] | None = None) -> ProviderResponse:
        messages = []
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=settings.model_max_tokens,
            timeout=settings.model_timeout,
        )

        text = _strip_thinking(response.choices[0].message.content)
        tokens = response.usage.total_tokens if response.usage else 0

        logger.info("Groq response: %d tokens", tokens)

        return ProviderResponse(
            text=text,
            model=self.model,
            provider=self.name,
            tokens_used=tokens,
        )

    async def health_check(self) -> bool:
        try:
            await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
                timeout=10,
            )
            return True
        except Exception as e:
            logger.warning("Groq health check failed: %s", e)
            return False
