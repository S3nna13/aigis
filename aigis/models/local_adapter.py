from __future__ import annotations

from aigis.models.base import Message, ModelAdapter, ModelResponse
from aigis.utils import CircuitBreaker, with_retry


class LocalAdapter(ModelAdapter):
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        retries: int = 3,
    ):
        self._model = model
        self._base_url = base_url or "http://localhost:8000/v1"
        self._api_key = api_key
        self._retries = retries
        self._cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)

    @property
    def model_name(self) -> str:
        return f"local/{self._model}"

    async def generate(self, messages: list[Message], **kwargs) -> ModelResponse:
        import httpx

        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.0),
            "max_tokens": kwargs.get("max_tokens"),
            "stream": False,
        }
        headers: dict = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        async def _call():
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                return resp.json()

        data = await self._cb.call(with_retry, _call, retries=self._retries)

        choice = data["choices"][0]
        usage_data = data.get("usage")
        return ModelResponse(
            content=choice["message"]["content"],
            usage=(
                {"prompt": usage_data["prompt_tokens"], "completion": usage_data["completion_tokens"]}
                if usage_data
                else None
            ),
            raw=data,
        )

    async def generate_with_logprobs(self, messages: list[Message], **kwargs) -> ModelResponse:
        import httpx

        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.0),
            "logprobs": True,
            "top_logprobs": kwargs.get("top_logprobs", 5),
            "stream": False,
        }
        headers: dict = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        async def _call():
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                return resp.json()

        data = await self._cb.call(with_retry, _call, retries=self._retries)

        choice = data["choices"][0]
        return ModelResponse(
            content=choice["message"]["content"],
            usage=None,
            raw=data,
        )
