from datetime import UTC, datetime

from opencs.agents.base_worker import WorkerInput
from opencs.agents.cs_reply import CSReplyWorker
from opencs.agents.llm_client import FakeLLMClient
from opencs.channel.schema import ContentPart, InboundMessage
from opencs.harness.action_plan import RiskTier


def _inbound(text: str = "hello") -> InboundMessage:
    return InboundMessage(
        channel_id="webchat",
        conversation_id="conv-1",
        customer_id="cust-1",
        sender_kind="customer",
        content=[ContentPart(kind="text", text=text)],
        timestamp=datetime(2026, 5, 1, tzinfo=UTC),
        raw_payload={},
        platform_meta={},
    )


async def test_cs_reply_produces_one_action_plan() -> None:
    llm = FakeLLMClient(responses=["Hi! How can I help you today?"])
    worker = CSReplyWorker(llm=llm, model="fake")
    plans = await worker.run(WorkerInput(message=_inbound("hello")))
    assert len(plans) == 1
    plan = plans[0]
    assert plan.tool_id == "channel.send"
    assert plan.risk_hint == RiskTier.ORANGE_C
    assert plan.args["conversation_id"] == "conv-1"
    assert plan.args["text"] == "Hi! How can I help you today?"


async def test_cs_reply_passes_customer_text_to_llm() -> None:
    llm = FakeLLMClient(responses=["Got it!"])
    worker = CSReplyWorker(llm=llm, model="fake")
    await worker.run(WorkerInput(message=_inbound("I need a refund")))
    last_call = llm.calls[-1]
    user_msg = next(m for m in last_call["messages"] if m.role == "user")
    assert "I need a refund" in user_msg.content


async def test_cs_reply_action_id_is_unique_per_call() -> None:
    llm = FakeLLMClient(responses=["ok", "ok"])
    worker = CSReplyWorker(llm=llm, model="fake")
    p1 = (await worker.run(WorkerInput(message=_inbound())))[0]
    p2 = (await worker.run(WorkerInput(message=_inbound())))[0]
    assert p1.action_id != p2.action_id


async def test_cs_reply_intent_is_non_empty() -> None:
    llm = FakeLLMClient(responses=["reply"])
    worker = CSReplyWorker(llm=llm, model="fake")
    plans = await worker.run(WorkerInput(message=_inbound()))
    assert plans[0].intent != ""


async def test_cs_reply_includes_l2_summary_in_prompt() -> None:
    llm = FakeLLMClient(responses=["Got it!"])
    worker = CSReplyWorker(llm=llm, model="fake")
    inp = WorkerInput(
        message=_inbound("hello"),
        session_context={
            "l2_summary": "Customer is VIP. Prefers email.",
            "skills": [],
        },
    )
    await worker.run(inp)
    system_msg = next(m for m in llm.calls[-1]["messages"] if m.role == "system")
    assert "VIP" in system_msg.content


async def test_cs_reply_includes_skill_text_in_prompt() -> None:
    llm = FakeLLMClient(responses=["No problem!"])
    worker = CSReplyWorker(llm=llm, model="fake")
    inp = WorkerInput(
        message=_inbound("I want a refund"),
        session_context={
            "l2_summary": None,
            "skills": ["Handle refunds carefully. Ask for order number."],
        },
    )
    await worker.run(inp)
    system_msg = next(m for m in llm.calls[-1]["messages"] if m.role == "system")
    assert "Handle refunds carefully" in system_msg.content


async def test_cs_reply_no_context_uses_base_prompt_only() -> None:
    llm = FakeLLMClient(responses=["Sure!"])
    worker = CSReplyWorker(llm=llm, model="fake")
    inp = WorkerInput(message=_inbound("help"))
    await worker.run(inp)
    system_msg = next(m for m in llm.calls[-1]["messages"] if m.role == "system")
    assert "customer service" in system_msg.content.lower()


async def test_order_reference_emits_crm_lookup_plan() -> None:
    llm = FakeLLMClient(responses=["Let me check your order."])
    worker = CSReplyWorker(llm=llm, model="fake")
    plans = await worker.run(WorkerInput(message=_inbound("what happened to ord-001?")))
    tool_ids = [p.tool_id for p in plans]
    assert "crm.get_order" in tool_ids
    assert "channel.send" in tool_ids


async def test_order_plan_is_green_tier() -> None:
    llm = FakeLLMClient(responses=["Checking order status."])
    worker = CSReplyWorker(llm=llm, model="fake")
    plans = await worker.run(WorkerInput(message=_inbound("track ord-002 please")))
    order_plans = [p for p in plans if p.tool_id == "crm.get_order"]
    assert len(order_plans) == 1
    assert order_plans[0].risk_hint == RiskTier.GREEN
    assert order_plans[0].args["order_id"] == "ord-002"


async def test_no_order_reference_emits_only_channel_send() -> None:
    llm = FakeLLMClient(responses=["Hi there!"])
    worker = CSReplyWorker(llm=llm, model="fake")
    plans = await worker.run(WorkerInput(message=_inbound("hello")))
    assert len(plans) == 1
    assert plans[0].tool_id == "channel.send"
