"""
Retry + circuit breaker utilities for model adapter calls.
"""

from __future__ import annotations

import asyncio
import enum
import time
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

import httpx


T = TypeVar("T")


class CircuitState(enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3
    _failures: int = field(default=0)
    _state: CircuitState = field(default=CircuitState.CLOSED)
    _last_failure_time: float = field(default=0.0)
    _half_open_calls: int = field(default=0)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                else:
                    raise CircuitOpenError("Circuit is OPEN")

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitOpenError("Circuit HALF_OPEN limit reached")
                self._half_open_calls += 1

        try:
            result = await fn(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as exc:
            await self._on_failure()
            raise exc

    async def _on_success(self) -> None:
        async with self._lock:
            self._failures = 0
            self._state = CircuitState.CLOSED

    async def _on_failure(self) -> None:
        async with self._lock:
            self._failures += 1
            self._last_failure_time = time.monotonic()
            if self._failures >= self.failure_threshold:
                self._state = CircuitState.OPEN


class CircuitOpenError(Exception):
    pass


async def with_retry(
    fn: Callable[..., Any],
    *args: Any,
    retries: int = 3,
    backoff: float = 1.0,
    exceptions: tuple = (httpx.HTTPStatusError, httpx.ConnectError, httpx.ConnectTimeout),
    **kwargs: Any,
) -> Any:
    """
    Retry an async function with exponential backoff.

    Args:
        fn: Async callable to retry.
        *args: Positional arguments for fn.
        retries: Number of retry attempts.
        backoff: Base backoff multiplier in seconds.
        exceptions: Tuple of exception types to catch and retry.
        **kwargs: Keyword arguments for fn.
    """
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return await fn(*args, **kwargs)
        except exceptions as exc:
            last_exc = exc
            if attempt < retries:
                sleep_time = backoff * (2**attempt)
                await asyncio.sleep(sleep_time)
            else:
                raise RetryExhaustedError(f"All {retries} retries failed") from last_exc
    raise RetryExhaustedError("Unexpected: no exception raised") from last_exc


class RetryExhaustedError(Exception):
    pass
