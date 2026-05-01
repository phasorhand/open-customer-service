from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class LLMMessage:
    role: str   # "system" | "user" | "assistant"
    content: str


@runtime_checkable
class LLMClient(Protocol):
    async def chat(self, *, messages: list[LLMMessage], model: str) -> str:
        """Return the assistant's text reply."""
        ...


class FakeLLMClient:
    """Scripted LLM client for testing. Cycles through `responses`."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self._index = 0
        self.calls: list[dict[str, Any]] = []

    async def chat(self, *, messages: list[LLMMessage], model: str) -> str:
        self.calls.append({"messages": messages, "model": model})
        reply = self._responses[self._index % len(self._responses)]
        self._index += 1
        return reply


class LiteLLMClient:
    """Production LLM client backed by litellm.acompletion."""

    def __init__(self, *, default_model: str = "claude-sonnet-4-6") -> None:
        self._default_model = default_model

    async def chat(self, *, messages: list[LLMMessage], model: str | None = None) -> str:
        import litellm  # lazy import — not available in all test envs

        response = await litellm.acompletion(
            model=model or self._default_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        content = response.choices[0].message.content
        return str(content) if content else ""
