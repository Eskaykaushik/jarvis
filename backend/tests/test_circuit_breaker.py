import time
from app.reliability.circuit_breaker import CircuitBreaker


def test_record_failure_opens_circuit():
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)
    for _ in range(3):
        cb.record_failure("groq")
    assert cb.is_open("groq") is True


def test_record_success_clears_failures():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure("groq")
    cb.record_failure("groq")
    cb.record_success("groq")
    assert cb.is_open("groq") is False
    assert cb.status().get("groq") != "degraded"


def test_circuit_closes_after_cooldown():
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=1)
    cb.record_failure("groq")
    cb.record_failure("groq")
    assert cb.is_open("groq") is True
    time.sleep(1.1)
    assert cb.is_open("groq") is False


def test_status_returns_degraded():
    cb = CircuitBreaker(failure_threshold=5)
    cb.record_failure("groq")
    assert cb.status()["groq"] == "degraded"


def test_status_returns_healthy_after_success():
    cb = CircuitBreaker(failure_threshold=5)
    cb.record_failure("groq")
    cb.record_success("groq")
    assert cb.status().get("groq") is None


def test_multiple_providers_independent():
    cb = CircuitBreaker(failure_threshold=2)
    cb.record_failure("groq")
    cb.record_failure("groq")
    cb.record_failure("openrouter")
    assert cb.is_open("groq") is True
    assert cb.is_open("openrouter") is False
