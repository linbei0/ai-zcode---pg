from __future__ import annotations

import time
from abc import ABC, abstractmethod

import redis


class RateLimiter(ABC):
    @abstractmethod
    def try_acquire(self, key: str, rate: int, interval_seconds: int) -> bool: ...


class InMemoryRateLimiter(RateLimiter):
    def __init__(self):
        self._store: dict[str, tuple[int, float]] = {}

    def try_acquire(self, key: str, rate: int, interval_seconds: int) -> bool:
        now = time.time()
        count, expires_at = self._store.get(key, (0, now + interval_seconds))
        if expires_at <= now:
            count = 0
            expires_at = now + interval_seconds
        count += 1
        self._store[key] = (count, expires_at)
        return count <= rate


class RedisRateLimiter(RateLimiter):
    def __init__(self, redis_url: str):
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)

    def try_acquire(self, key: str, rate: int, interval_seconds: int) -> bool:
        pipeline = self.client.pipeline()
        pipeline.incr(key)
        pipeline.ttl(key)
        count, ttl = pipeline.execute()
        if ttl == -1:
            self.client.expire(key, interval_seconds)
        return int(count) <= rate
