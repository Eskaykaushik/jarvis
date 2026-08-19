from abc import ABC, abstractmethod

from pydantic import BaseModel


class ProviderResponse(BaseModel):
    text: str
    model: str
    provider: str
    tokens_used: int = 0


class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str, context: list[dict] | None = None) -> ProviderResponse:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...
