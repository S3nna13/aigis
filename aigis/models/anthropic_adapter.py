from __future__ import annotations

from typing import TYPE_CHECKING

from aigis.models.base import Message, ModelAdapter, ModelResponse

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic


class AnthropicAdapter(ModelAdapter):
    def __init__(self, model: str, api_key: str | None = None, base_url: str | None = None):
        self._model = model
        self._api_key = api_key
        self._base_url = base_url
        self._client: AsyncAnthropic | None = None

    async def _ensure_client(self) -> AsyncAnthropic:
        if self._client is None:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=self._api_key, base_url=self._base_url)
        return self._client

    @property
    def model_name(self) -> str:
        return f"anthropic/{self._model}"

    async def generate(self, messages: list[Message], **kwargs) -> ModelResponse:
        client = await self._ensure_client()

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

        raw = await client.messages.create(**params)
        content = raw.content[0].text if raw.content else ""
        return ModelResponse(
            content=content,
            usage={"prompt": raw.usage.input_tokens, "completion": raw.usage.output_tokens}
            if raw.usage
            else None,
            raw=raw.model_dump() if hasattr(raw, "model_dump") else None,
        )

    async def generate_with_logprobs(self, messages: list[Message], **kwargs) -> ModelResponse:
        client = await self._ensure_client()

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

        raw = await client.messages.create(**params)
        content = raw.content[0].text if raw.content else ""
        return ModelResponse(
            content=content,
            usage=None,
            raw=raw.model_dump() if hasattr(raw, "model_dump") else None,
        )
