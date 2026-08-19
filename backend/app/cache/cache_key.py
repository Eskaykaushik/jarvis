import hashlib
import json


def make_cache_key(prefix: str, prompt: str, context: list[dict] | None = None) -> str:
    content = {"prompt": prompt, "context": context or []}
    raw = json.dumps(content, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"{prefix}:{digest}"
