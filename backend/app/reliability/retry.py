import asyncio
import logging
import random

logger = logging.getLogger(__name__)


def with_retry(
    max_retries: int = 2,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        jitter = random.uniform(0, delay * 0.5)
                        wait = delay + jitter
                        logger.warning(
                            "Attempt %d/%d failed for %s: %s. Retrying in %.1fs",
                            attempt + 1,
                            max_retries + 1,
                            func.__qualname__,
                            e,
                            wait,
                        )
                        await asyncio.sleep(wait)
            raise last_exception
        return wrapper
    return decorator
