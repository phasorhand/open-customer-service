from __future__ import annotations

from opencs.agents.llm_client import LLMClient, LLMMessage
from opencs.replay.types import ReplayMode


class ReplayingLLMClient:
    """LLM client wrapper for replay: serves cached responses or delegates to real LLM.

    - STRICT mode: always serve from cache (sequential); fall back if cache exhausted.
    - WHAT_IF / PARTIAL mode: always call the real LLM (with optional overrides).
    """

    def __init__(
        self,
        *,
        mode: ReplayMode,
        llm_cache: list[str],
        fallback: LLMClient,
        model_override: str | None = None,
        prompt_override: str | None = None,
    ) -> None:
        self._mode = mode
        self._cache = list(llm_cache)
        self._cache_index = 0
        self._fallback = fallback
        self._model_override = model_override
        self._prompt_override = prompt_override

    async def chat(self, *, messages: list[LLMMessage], model: str) -> str:
        if self._mode == ReplayMode.STRICT:
            if self._cache_index < len(self._cache):
                result = self._cache[self._cache_index]
                self._cache_index += 1
                return result
            return await self._fallback.chat(messages=messages, model=model)

        effective_model = self._model_override or model
        effective_messages = self._apply_prompt_override(messages)
        return await self._fallback.chat(messages=effective_messages, model=effective_model)

    def _apply_prompt_override(self, messages: list[LLMMessage]) -> list[LLMMessage]:
        if not self._prompt_override:
            return messages
        if messages and messages[0].role == "system":
            return [LLMMessage(role="system", content=self._prompt_override)] + list(messages[1:])
        return [LLMMessage(role="system", content=self._prompt_override)] + list(messages)
