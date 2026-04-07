import fakeredis

from app.core.rate_limit import RedisRateLimiter


def test_redis_rate_limiter_uses_python_namespace_to_avoid_java_key_collision(monkeypatch) -> None:
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    fake_redis.hset("rate_limit:user:123", mapping={"value": "java-redisson"})

    monkeypatch.setattr("app.core.rate_limit.redis.Redis.from_url", lambda *args, **kwargs: fake_redis)

    limiter = RedisRateLimiter("redis://unused")

    assert limiter.try_acquire("py_rate_limit:chat:user:123", rate=5, interval_seconds=60) is True
    assert fake_redis.type("rate_limit:user:123") == "hash"
    assert fake_redis.type("py_rate_limit:chat:user:123") == "string"


def test_redis_rate_limiter_repairs_wrongtype_key_and_retries(monkeypatch) -> None:
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    fake_redis.hset("py_rate_limit:chat:user:456", mapping={"value": "bad-state"})

    monkeypatch.setattr("app.core.rate_limit.redis.Redis.from_url", lambda *args, **kwargs: fake_redis)

    limiter = RedisRateLimiter("redis://unused")

    assert limiter.try_acquire("py_rate_limit:chat:user:456", rate=5, interval_seconds=60) is True
    assert fake_redis.type("py_rate_limit:chat:user:456") == "string"
    assert fake_redis.get("py_rate_limit:chat:user:456") == "1"
