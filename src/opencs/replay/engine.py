from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from opencs.agents.cs_reply import CSReplyWorker
from opencs.agents.orchestrator import Orchestrator
from opencs.channel.registry import ChannelRegistry
from opencs.channel.schema import ContentPart, InboundMessage
from opencs.harness.action_guard import ActionGuard
from opencs.harness.audit_log import AuditLog
from opencs.harness.hitl_queue import HITLQueue
from opencs.harness.token import TokenFactory
from opencs.memory.l0_store import L0Event, L0RawEventStore
from opencs.memory.memory_store import MemoryStore
from opencs.replay.differ import ReplayDiffer
from opencs.replay.read_only_channel import ReadOnlyChannelAdapter
from opencs.replay.replaying_llm import ReplayingLLMClient
from opencs.replay.replaying_tool import ReplayingToolExecutor
from opencs.replay.trace_loader import TraceLoader
from opencs.replay.types import ReplayMode, ReplayResult, ReplaySession, Verdict
from opencs.tools.executor import ToolExecutor
from opencs.tools.registry import ToolRegistry

if TYPE_CHECKING:
    from opencs.agents.llm_client import LLMClient


_REPLAY_SECRET = b"replay-engine-internal"


class ReplayEngine:
    def __init__(
        self,
        *,
        l0: L0RawEventStore,
        tool_registry: ToolRegistry,
        llm_fallback: LLMClient,
    ) -> None:
        self._l0 = l0
        self._tool_registry = tool_registry
        self._llm_fallback = llm_fallback
        self._trace_loader = TraceLoader(l0=l0)

    async def replay(self, session: ReplaySession) -> ReplayResult:
        session_id = f"replay-{uuid.uuid4().hex[:12]}"

        trace = self._trace_loader.load(session.source_conversation_id)
        if not trace.events:
            return ReplayResult(
                session_id=session_id,
                verdict=Verdict.INCONCLUSIVE,
                divergence_points=[],
                replay_event_count=0,
                baseline_event_count=0,
            )

        replaying_llm = ReplayingLLMClient(
            mode=session.mode,
            llm_cache=list(trace.llm_cache.values()),
            fallback=self._llm_fallback,
            model_override=session.overrides.model_override,
            prompt_override=session.overrides.prompt_override,
        )

        real_executor = ToolExecutor(registry=self._tool_registry)
        replaying_tool = ReplayingToolExecutor(
            mode=session.mode,
            tool_cache=trace.tool_cache,
            real_executor=real_executor,
            tool_ids_to_rerun=session.overrides.tool_ids_to_rerun,
        )

        replay_memory = MemoryStore()
        ro_adapter = ReadOnlyChannelAdapter()
        channel_registry = ChannelRegistry()
        channel_registry.register(ro_adapter)

        guard = ActionGuard(
            token_factory=TokenFactory(secret_key=_REPLAY_SECRET),
            audit_log=AuditLog(db_path=":memory:"),
            hitl_queue=HITLQueue(),
        )

        worker = CSReplyWorker(llm=replaying_llm, model="replay")
        orch = Orchestrator(
            workers=[worker],
            guard=guard,
            registry=channel_registry,
            memory_store=replay_memory,
            tool_executor=replaying_tool,
        )

        for inbound_event in trace.inbound_messages:
            msg = self._event_to_inbound_message(inbound_event, session.source_conversation_id)
            await orch.handle(message=msg)

        replay_events = replay_memory.l0.list(conversation_id=session.source_conversation_id)

        differ = ReplayDiffer()
        diff_result = differ.diff(baseline=trace.events, replay=replay_events)

        return ReplayResult(
            session_id=session_id,
            verdict=diff_result.verdict,
            divergence_points=diff_result.divergence_points,
            replay_event_count=len(replay_events),
            baseline_event_count=len(trace.events),
        )

    def _event_to_inbound_message(self, event: L0Event, conversation_id: str) -> InboundMessage:
        text = event.payload.get("text", "")
        customer_id = event.payload.get("customer_id", "unknown")
        return InboundMessage(
            channel_id="replay_readonly",
            conversation_id=conversation_id,
            customer_id=str(customer_id),
            sender_kind="customer",
            content=[ContentPart(kind="text", text=str(text) if text else ".")],
            timestamp=event.ts,
            raw_payload={},
            platform_meta={},
        )
