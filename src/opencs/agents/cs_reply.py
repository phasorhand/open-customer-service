import uuid

from opencs.agents.base_worker import BaseWorker, WorkerInput
from opencs.agents.llm_client import LLMClient, LLMMessage
from opencs.harness.action_plan import ActionPlan, RiskTier

_SYSTEM_PROMPT = """\
You are a helpful customer service agent. Reply to the customer's message concisely and professionally.
Do not make promises about refunds, discounts, or timelines without explicit confirmation.
Reply in the same language as the customer."""


class CSReplyWorker(BaseWorker):
    """Generates a customer-facing reply via LLM, submits as Orange-C ActionPlan."""

    worker_id = "cs_reply"

    def __init__(self, *, llm: LLMClient, model: str) -> None:
        self._llm = llm
        self._model = model

    async def run(self, inp: WorkerInput) -> list[ActionPlan]:
        customer_text = " ".join(
            part.text or "" for part in inp.message.content if part.kind == "text"
        ).strip()
        messages = [
            LLMMessage(role="system", content=_SYSTEM_PROMPT),
            LLMMessage(role="user", content=customer_text),
        ]
        reply_text = await self._llm.chat(messages=messages, model=self._model)
        action_id = f"cs-reply-{uuid.uuid4().hex[:12]}"
        plan = ActionPlan(
            action_id=action_id,
            tool_id="channel.send",
            args={
                "conversation_id": inp.message.conversation_id,
                "text": reply_text,
            },
            intent="Send LLM-generated reply to customer",
            risk_hint=RiskTier.ORANGE_C,
        )
        return [plan]
