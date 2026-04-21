# TODO: cache tests
import pytest
import time

from ttl_cache import TTLCache


def test_set_and_get_basic():
    """set/get en temel senaryosu."""
    cache = TTLCache()
    cache.set("key", "value")
    assert cache.get("key") == "value"


def test_get_missing_key_returns_default():
    """Olmayan key için default dönmeli."""
    cache = TTLCache()
    assert cache.get("nope") is None
    assert cache.get("nope", default="fallback") == "fallback"


def test_delete_existing_key():
    """Delete varsa True döner, sonra get default verir."""
    cache = TTLCache()
    cache.set("key", 1)
    assert cache.delete("key") is True
    assert cache.get("key") is None
def test_delete_missing_key_returns_false():
    cache = TTLCache()
    assert cache.delete("nope") is False

def test_contains_operator():
    cache = TTLCache()
    cache.set("key", "value")
    assert "key" in cache
    assert "nope" not in cache
import time

def test_ttl_expiration():
    cache = TTLCache(default_ttl=0.05)   # 50ms TTL
    cache.set("key", "value")
    assert cache.get("key") == "value"   # henüz expire olmadı
    time.sleep(0.1)                      # 100ms bekle → TTL dolmuş olmalı
    assert cache.get("key") is None      # expire → default None
def test_invalid_ttl_raises():
    with pytest.raises(ValueError):
        TTLCache(default_ttl=0)
def test_invalid_ttl_raises():
    with pytest.raises(ValueError):
        TTLCache(default_ttl=0)
def test_invalid_ttl_raises2():
    with pytest.raises(ValueError):
        TTLCache(default_ttl=-1)
