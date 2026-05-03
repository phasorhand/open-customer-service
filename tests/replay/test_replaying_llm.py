import pytest

from opencs.agents.llm_client import FakeLLMClient, LLMMessage
from opencs.replay.replaying_llm import ReplayingLLMClient
from opencs.replay.types import ReplayMode


def _msgs(text: str) -> list[LLMMessage]:
    return [LLMMessage(role="user", content=text)]


async def test_strict_mode_serves_from_cache() -> None:
    cache = ["Cached response one", "Cached response two"]
    client = ReplayingLLMClient(
        mode=ReplayMode.STRICT,
        llm_cache=cache,
        fallback=FakeLLMClient(responses=["SHOULD NOT APPEAR"]),
    )
    result = await client.chat(messages=_msgs("hello"), model="fake")
    assert result == "Cached response one"


async def test_strict_mode_iterates_cache_sequentially() -> None:
    cache = ["First", "Second"]
    client = ReplayingLLMClient(
        mode=ReplayMode.STRICT,
        llm_cache=cache,
        fallback=FakeLLMClient(responses=["fallback"]),
    )
    r1 = await client.chat(messages=_msgs("a"), model="fake")
    r2 = await client.chat(messages=_msgs("b"), model="fake")
    assert r1 == "First"
    assert r2 == "Second"


async def test_strict_mode_falls_back_when_cache_exhausted() -> None:
    cache = ["Only one"]
    fallback = FakeLLMClient(responses=["Fallback response"])
    client = ReplayingLLMClient(
        mode=ReplayMode.STRICT,
        llm_cache=cache,
        fallback=fallback,
    )
    await client.chat(messages=_msgs("a"), model="fake")
    r2 = await client.chat(messages=_msgs("b"), model="fake")
    assert r2 == "Fallback response"


async def test_what_if_mode_calls_real_llm() -> None:
    cache = ["Cached"]
    fallback = FakeLLMClient(responses=["Real LLM output"])
    client = ReplayingLLMClient(
        mode=ReplayMode.WHAT_IF,
        llm_cache=cache,
        fallback=fallback,
    )
    result = await client.chat(messages=_msgs("hello"), model="fake")
    assert result == "Real LLM output"
    assert len(fallback.calls) == 1


async def test_partial_mode_calls_real_llm() -> None:
    cache = ["Cached"]
    fallback = FakeLLMClient(responses=["Real"])
    client = ReplayingLLMClient(
        mode=ReplayMode.PARTIAL,
        llm_cache=cache,
        fallback=fallback,
    )
    result = await client.chat(messages=_msgs("x"), model="fake")
    assert result == "Real"


async def test_model_override_applied() -> None:
    fallback = FakeLLMClient(responses=["response"])
    client = ReplayingLLMClient(
        mode=ReplayMode.WHAT_IF,
        llm_cache=[],
        fallback=fallback,
        model_override="gpt-4o",
    )
    await client.chat(messages=_msgs("x"), model="original-model")
    assert fallback.calls[0]["model"] == "gpt-4o"


async def test_prompt_override_prepended() -> None:
    fallback = FakeLLMClient(responses=["response"])
    client = ReplayingLLMClient(
        mode=ReplayMode.WHAT_IF,
        llm_cache=[],
        fallback=fallback,
        prompt_override="You are now very strict.",
    )
    msgs = [LLMMessage(role="system", content="Original prompt"), LLMMessage(role="user", content="hi")]
    await client.chat(messages=msgs, model="fake")
    sent_msgs = fallback.calls[0]["messages"]
    assert sent_msgs[0].content == "You are now very strict."
