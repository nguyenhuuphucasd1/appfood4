from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request

from backend.config import AUTH_RATE_LIMIT_PER_MINUTE, PREDICT_RATE_LIMIT_PER_MINUTE


class InMemoryRateLimiter:
    """Small per-process limiter for local and single-instance deployments."""

    def __init__(self) -> None:
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, request: Request, *, bucket: str, limit: int, window: int = 60) -> None:
        if limit <= 0:
            return
        client = request.client.host if request.client else "unknown"
        key = (bucket, client)
        now = monotonic()
        with self._lock:
            events = self._events[key]
            while events and events[0] <= now - window:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(window - (now - events[0])))
                raise HTTPException(
                    status_code=429,
                    detail="Bạn thao tác quá nhanh. Vui lòng thử lại sau.",
                    headers={"Retry-After": str(retry_after)},
                )
            events.append(now)


limiter = InMemoryRateLimiter()


def auth_rate_limit(request: Request) -> None:
    limiter.check(request, bucket="auth", limit=AUTH_RATE_LIMIT_PER_MINUTE)


def predict_rate_limit(request: Request) -> None:
    limiter.check(request, bucket="predict", limit=PREDICT_RATE_LIMIT_PER_MINUTE)
