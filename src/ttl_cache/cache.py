# TODO: TTLCache implementation
from __future__ import annotations

import threading
import time
from typing import Any, Hashable

_MISSING = object()


class TTLCache:
    """Thread-safe in-memory cache with per-key TTL.

    TTL is checked lazily on access — expired entries are removed
    when accessed, not via a background sweeper.
    """

    def __init__(self, default_ttl: float | None = None) -> None:
        if default_ttl is not None and default_ttl <= 0:
            raise ValueError("default_ttl must be positive or None")
        self._default_ttl = default_ttl
        self._data: dict[Hashable, tuple[Any, float | None]] = {}
        self._lock = threading.RLock()

    def set(self, key: Hashable, value: Any, ttl: float | None = None) -> None:
        """Store value under key. `ttl` overrides `default_ttl` if given."""
        effective_ttl = ttl if ttl is not None else self._default_ttl
        if effective_ttl is not None and effective_ttl <= 0:
            raise ValueError("ttl must be positive or None")
        expires_at = (
            time.monotonic() + effective_ttl if effective_ttl is not None else None
        )
        with self._lock:
            self._data[key] = (value, expires_at)

    def get(self, key: Hashable, default: Any = None) -> Any:
        """Return value for key, or `default` if missing or expired."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return default
            value, expires_at = entry
            if expires_at is not None and time.monotonic() >= expires_at:
                del self._data[key]
                return default
            return value

    def delete(self, key: Hashable) -> bool:
        """Remove key. Return True if key existed, False otherwise."""
        with self._lock:
            return self._data.pop(key, None) is not None

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)

    def __contains__(self, key: Hashable) -> bool:
        return self.get(key, _MISSING) is not _MISSING