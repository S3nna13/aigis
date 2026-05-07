from __future__ import annotations

from typing import TYPE_CHECKING

from aigis.models.base import Message, ModelAdapter, ModelResponse

if TYPE_CHECKING:
    from openai import AsyncOpenAI


class OpenAIAdapter(ModelAdapter):
    def __init__(self, model: str, api_key: str | None = None, base_url: str | None = None):
        self._model = model
        self._api_key = api_key
        self._base_url = base_url
        self._client: AsyncOpenAI | None = None

    async def _ensure_client(self) -> AsyncOpenAI:
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
        return self._client

    @property
    def model_name(self) -> str:
        return f"openai/{self._model}"

    async def generate(self, messages: list[Message], **kwargs) -> ModelResponse:
        client = await self._ensure_client()
        raw = await client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],  # type: ignore[misc]
            temperature=kwargs.get("temperature", 0.0),
            max_tokens=kwargs.get("max_tokens"),
        )
        choice = raw.choices[0]
        return ModelResponse(
            content=choice.message.content or "",
            usage={"prompt": raw.usage.prompt_tokens, "completion": raw.usage.completion_tokens}
            if raw.usage
            else None,
            raw=raw.model_dump() if hasattr(raw, "model_dump") else None,
        )

    async def generate_with_logprobs(self, messages: list[Message], **kwargs) -> ModelResponse:
        client = await self._ensure_client()
        raw = await client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],  # type: ignore[misc]
            temperature=kwargs.get("temperature", 0.0),
            logprobs=True,
            top_logprobs=kwargs.get("top_logprobs", 5),
        )
        choice = raw.choices[0]
        return ModelResponse(
            content=choice.message.content or "",
            usage=None,
            raw=raw.model_dump() if hasattr(raw, "model_dump") else None,
        )
