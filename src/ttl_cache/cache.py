from __future__ import annotations

import threading
import time
from typing import Any, Hashable

_MISSING = object()


class _Node:
    """Doubly linked list node. Internal only."""

    __slots__ = ("key", "value", "expires_at", "prev", "next")

    def __init__(
        self,
        key: Hashable,
        value: Any,
        expires_at: float | None,
    ) -> None:
        self.key = key
        self.value = value
        self.expires_at = expires_at
        self.prev: _Node | None = None
        self.next: _Node | None = None


class TTLCache:
    """Thread-safe in-memory cache with per-key TTL and LRU ordering.

    TTL is checked lazily on access. LRU ordering is maintained via
    a doubly linked list with sentinel head and tail nodes.
    """

    def __init__(self, default_ttl: float | None = None) -> None:
        if default_ttl is not None and default_ttl <= 0:
            raise ValueError("default_ttl must be positive or None")
        self._default_ttl = default_ttl
        self._data: dict[Hashable, _Node] = {}
        self._lock = threading.RLock()

        # Sentinel head and tail — always present, never hold real data.
        # head.next = most recently used, tail.prev = least recently used.
        self._head: _Node = _Node(None, None, None)
        self._tail: _Node = _Node(None, None, None)
        self._head.next = self._tail
        self._tail.prev = self._head

    # --- Internal linked-list helpers ---

    def _remove(self, node: _Node) -> None:
        """Detach node from the linked list."""
        assert node.prev is not None and node.next is not None
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_to_front(self, node: _Node) -> None:
        """Insert node right after head (most recently used position)."""
        node.prev = self._head
        node.next = self._head.next
        assert self._head.next is not None
        self._head.next.prev = node
        self._head.next = node

    def _move_to_front(self, node: _Node) -> None:
        """Mark node as most recently used."""
        self._remove(node)
        self._add_to_front(node)

    # --- Public API ---

    def set(self, key: Hashable, value: Any, ttl: float | None = None) -> None:
        effective_ttl = ttl if ttl is not None else self._default_ttl
        if effective_ttl is not None and effective_ttl <= 0:
            raise ValueError("ttl must be positive or None")
        expires_at = (
            time.monotonic() + effective_ttl if effective_ttl is not None else None
        )
        with self._lock:
            existing = self._data.get(key)
            if existing is not None:
                existing.value = value
                existing.expires_at = expires_at
                self._move_to_front(existing)
            else:
                node = _Node(key, value, expires_at)
                self._add_to_front(node)
                self._data[key] = node

    def get(self, key: Hashable, default: Any = None) -> Any:
        with self._lock:
            node = self._data.get(key)
            if node is None:
                return default
            if node.expires_at is not None and time.monotonic() >= node.expires_at:
                self._remove(node)
                del self._data[key]
                return default
            self._move_to_front(node)
            return node.value

    def delete(self, key: Hashable) -> bool:
        with self._lock:
            node = self._data.pop(key, None)
            if node is None:
                return False
            self._remove(node)
            return True

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)

    def __contains__(self, key: Hashable) -> bool:
        return self.get(key, _MISSING) is not _MISSING