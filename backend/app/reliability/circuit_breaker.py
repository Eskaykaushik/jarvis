import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    cooldown_seconds: int = 300
    _failures: dict[str, list[float]] = field(default_factory=dict)
    _open_until: dict[str, float] = field(default_factory=dict)

    def record_failure(self, provider: str):
        now = time.time()
        self._failures.setdefault(provider, [])
        self._failures[provider].append(now)
        self._failures[provider] = [
            t for t in self._failures[provider] if now - t < self.cooldown_seconds
        ]
        if len(self._failures[provider]) >= self.failure_threshold:
            self._open_until[provider] = now + self.cooldown_seconds
            logger.warning("Circuit OPEN for %s for %ds", provider, self.cooldown_seconds)

    def record_success(self, provider: str):
        self._failures.pop(provider, None)
        self._open_until.pop(provider, None)

    def is_open(self, provider: str) -> bool:
        now = time.time()
        open_until = self._open_until.get(provider, 0)
        if now < open_until:
            return True
        if open_until > 0:
            self._open_until.pop(provider, None)
            logger.info("Circuit CLOSED for %s", provider)
        return False

    def status(self) -> dict[str, str]:
        now = time.time()
        result = {}
        all_providers = set(list(self._failures.keys()) + list(self._open_until.keys()))
        for p in all_providers:
            if now < self._open_until.get(p, 0):
                result[p] = "open"
            elif len(self._failures.get(p, [])) > 0:
                result[p] = "degraded"
            else:
                result[p] = "healthy"
        return result
