"""
Webhook system for guardrail alerts and eval completion events.
Supports synchronous (blocking) and asynchronous (fire-and-forget) delivery.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx


class WebhookEvent(str, Enum):
    GUARDRAIL_TRIGGERED = "guardrail.triggered"
    GUARDRAIL_PASSED = "guardrail.passed"
    EVAL_COMPLETED = "eval.completed"
    EVAL_FAILED = "eval.failed"
    PIPELINE_COMPLETED = "pipeline.completed"


@dataclass
class WebhookPayload:
    event: WebhookEvent
    source: str
    timestamp: str
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event.value,
            "source": self.source,
            "timestamp": self.timestamp,
            "data": self.data,
        }


@dataclass
class WebhookConfig:
    url: str
    secret: str | None = None
    retries: int = 3
    timeout: float = 10.0
    async_delivery: bool = True


@dataclass
class WebhookManager:
    _hooks: list[WebhookConfig] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def register(self, config: WebhookConfig) -> None:
        self._hooks.append(config)

    def unregister(self, url: str) -> None:
        self._hooks = [h for h in self._hooks if h.url != url]

    async def dispatch(self, payload: WebhookPayload) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for hook in self._hooks:
            try:
                result = await self._send(hook, payload)
                results[hook.url] = {"status": "ok", "response": result}
            except Exception as exc:  # noqa: BLE001
                results[hook.url] = {"status": "error", "error": str(exc)}
        return results

    async def _send(self, hook: WebhookConfig, payload: WebhookPayload) -> dict[str, Any]:
        body = json.dumps(payload.to_dict())
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AIGIS-Webhook/0.1",
            "X-AIGIS-Event": payload.event.value,
        }
        if hook.secret:
            signature = hmac.new(hook.secret.encode(), body.encode(), hashlib.sha256).hexdigest()
            headers["X-AIGIS-Signature"] = f"sha256={signature}"

        async with httpx.AsyncClient(timeout=hook.timeout) as client:
            for attempt in range(hook.retries):
                try:
                    resp = await client.post(hook.url, content=body, headers=headers)
                    resp.raise_for_status()
                    return {"status_code": resp.status_code, "body": resp.text[:500]}
                except (httpx.HTTPStatusError, httpx.ConnectError, httpx.ConnectTimeout):
                    if attempt == hook.retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)
            raise RuntimeError("Webhook delivery failed after all retries")


_default_manager = WebhookManager()


def get_webhook_manager() -> WebhookManager:
    return _default_manager


async def dispatch_webhook(event: WebhookEvent, source: str, data: dict[str, Any]) -> dict[str, Any]:
    from datetime import datetime, timezone

    payload = WebhookPayload(
        event=event,
        source=source,
        timestamp=datetime.now(timezone.utc).isoformat(),
        data=data,
    )
    return await _default_manager.dispatch(payload)
