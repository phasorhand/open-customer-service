from opencs.agents.llm_client import FakeLLMClient, LLMMessage


async def test_fake_client_returns_scripted_response() -> None:
    client = FakeLLMClient(responses=["Hello, how can I help?"])
    messages = [LLMMessage(role="user", content="hi")]
    reply = await client.chat(messages=messages, model="fake")
    assert reply == "Hello, how can I help?"


async def test_fake_client_cycles_responses() -> None:
    client = FakeLLMClient(responses=["A", "B"])
    msgs = [LLMMessage(role="user", content="x")]
    r1 = await client.chat(messages=msgs, model="fake")
    r2 = await client.chat(messages=msgs, model="fake")
    r3 = await client.chat(messages=msgs, model="fake")
    assert r1 == "A"
    assert r2 == "B"
    assert r3 == "A"  # wraps around


async def test_fake_client_records_calls() -> None:
    client = FakeLLMClient(responses=["ok"])
    msgs = [LLMMessage(role="user", content="hello")]
    await client.chat(messages=msgs, model="test-model")
    assert len(client.calls) == 1
    assert client.calls[0]["model"] == "test-model"
    assert client.calls[0]["messages"] == msgs
