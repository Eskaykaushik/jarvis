import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.cache.cache_key import make_cache_key


def test_cache_key_deterministic():
    key1 = make_cache_key("chat", "hello", [{"role": "user", "content": "hi"}])
    key2 = make_cache_key("chat", "hello", [{"role": "user", "content": "hi"}])
    assert key1 == key2


def test_cache_key_different_prefix():
    key1 = make_cache_key("chat", "hello")
    key2 = make_cache_key("summary", "hello")
    assert key1 != key2


def test_cache_key_different_prompt():
    key1 = make_cache_key("chat", "hello")
    key2 = make_cache_key("chat", "world")
    assert key1 != key2


def test_cache_key_starts_with_prefix():
    key = make_cache_key("chat", "test")
    assert key.startswith("chat:")


def test_cache_key_length():
    key = make_cache_key("chat", "test")
    prefix, hash_part = key.split(":")
    assert len(hash_part) == 16
