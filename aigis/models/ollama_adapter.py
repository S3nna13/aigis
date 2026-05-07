from __future__ import annotations

from typing import TYPE_CHECKING

from aigis.models.base import Message, ModelAdapter, ModelResponse
from aigis.utils import CircuitBreaker, with_retry

if TYPE_CHECKING:
    from ollama import AsyncClient


class OllamaAdapter(ModelAdapter):
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        retries: int = 3,
    ):
        self._model = model
        self._base_url = base_url or "http://localhost:11434"
        self._retries = retries
        self._client: AsyncClient | None = None
        self._cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)

    async def _ensure_client(self) -> AsyncClient:
        if self._client is None:
            from ollama import AsyncClient

            self._client = AsyncClient(host=self._base_url)
        return self._client

    @property
    def model_name(self) -> str:
        return f"ollama/{self._model}"

    async def generate(self, messages: list[Message], **kwargs) -> ModelResponse:
        client = await self._ensure_client()
        formatted = [{"role": m.role, "content": m.content} for m in messages]

        async def _call():
            return await client.chat(
                model=self._model,
                messages=formatted,
                options={
                    "temperature": kwargs.get("temperature", 0.0),
                    "num_predict": kwargs.get("max_tokens", 2048),
                },
            )

        response = await self._cb.call(with_retry, _call, retries=self._retries)
        return ModelResponse(
            content=response.message.content or "",
            usage={
                "prompt": response.prompt_eval_count or 0,
                "completion": response.eval_count or 0,
            }
            if response.prompt_eval_count is not None
            else None,
            raw=response.model_dump() if hasattr(response, "model_dump") else None,
        )

    async def generate_with_logprobs(self, messages: list[Message], **kwargs) -> ModelResponse:
        return await self.generate(messages, **kwargs)
