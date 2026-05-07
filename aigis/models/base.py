from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str


@dataclass
class ModelResponse:
    content: str
    usage: dict | None = None
    raw: dict | None = None


class ModelAdapter(ABC):
    @abstractmethod
    async def generate(self, messages: list[Message], **kwargs) -> ModelResponse: ...

    @abstractmethod
    async def generate_with_logprobs(self, messages: list[Message], **kwargs) -> ModelResponse: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...
