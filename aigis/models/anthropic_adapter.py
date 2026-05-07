from __future__ import annotations

from typing import TYPE_CHECKING

from aigis.models.base import Message, ModelAdapter, ModelResponse
from aigis.utils import CircuitBreaker, with_retry

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic


class AnthropicAdapter(ModelAdapter):
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        retries: int = 3,
        timeout: float = 60.0,
    ):
        self._model = model
        self._api_key = api_key
        self._base_url = base_url
        self._retries = retries
        self._timeout = timeout
        self._client: AsyncAnthropic | None = None
        self._cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)

    async def _ensure_client(self) -> AsyncAnthropic:
        if self._client is None:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=self._api_key, base_url=self._base_url, timeout=self._timeout)
        return self._client

    @property
    def model_name(self) -> str:
        return f"anthropic/{self._model}"

    async def _make_params(self, messages: list[Message], kwargs: dict) -> dict:
        system_text = None
        user_messages = []
        for m in messages:
            if m.role == "system":
                system_text = m.content
            else:
                user_messages.append({"role": m.role, "content": m.content})

        params: dict = {
            "model": self._model,
            "messages": user_messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        if system_text:
            params["system"] = system_text
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        return params

    async def generate(self, messages: list[Message], **kwargs) -> ModelResponse:
        client = await self._ensure_client()
        params = await self._make_params(messages, kwargs)

        async def _call():
            return await client.messages.create(**params)

        raw = await self._cb.call(with_retry, _call, retries=self._retries)
        content = raw.content[0].text if raw.content else ""
        return ModelResponse(
            content=content,
            usage={"prompt": raw.usage.input_tokens, "completion": raw.usage.output_tokens}
            if raw.usage
            else None,
            raw=raw.model_dump() if hasattr(raw, "model_dump") else None,
        )

    async def generate_with_logprobs(self, messages: list[Message], **kwargs) -> ModelResponse:
        return await self.generate(messages, **kwargs)
