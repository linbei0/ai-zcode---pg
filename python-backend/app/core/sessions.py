from __future__ import annotations

import secrets
from abc import ABC, abstractmethod

import redis


class SessionStore(ABC):
    @abstractmethod
    def set_user_id(self, session_id: str, user_id: int, ttl_seconds: int) -> None: ...

    @abstractmethod
    def get_user_id(self, session_id: str) -> int | None: ...

    @abstractmethod
    def delete(self, session_id: str) -> None: ...


class RedisSessionStore(SessionStore):
    def __init__(self, redis_url: str):
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)

    def _key(self, session_id: str) -> str:
        return f"aizcode:session:{session_id}"

    def set_user_id(self, session_id: str, user_id: int, ttl_seconds: int) -> None:
        self.client.setex(self._key(session_id), ttl_seconds, user_id)

    def get_user_id(self, session_id: str) -> int | None:
        value = self.client.get(self._key(session_id))
        return int(value) if value else None

    def delete(self, session_id: str) -> None:
        self.client.delete(self._key(session_id))


class InMemorySessionStore(SessionStore):
    def __init__(self):
        self._store: dict[str, int] = {}

    def set_user_id(self, session_id: str, user_id: int, ttl_seconds: int) -> None:
        self._store[session_id] = user_id

    def get_user_id(self, session_id: str) -> int | None:
        return self._store.get(session_id)

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)


def generate_session_id() -> str:
    return secrets.token_urlsafe(32)
