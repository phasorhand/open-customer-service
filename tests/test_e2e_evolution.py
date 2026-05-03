"""E2E Evolution: three scenarios testing the full Proposal -> Gate -> Handler pipeline."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from opencs.evolution.gate import EvolutionGate
from opencs.evolution.handlers.memory import MemoryProposalHandler
from opencs.evolution.handlers.skill import SkillProposalHandler
from opencs.evolution.hitl_queue import EvolutionHITLQueue
from opencs.evolution.shadow_runner import ShadowRunner
from opencs.evolution.types import (
    EvolutionDimension,
    GateDecision,
    Proposal,
    ProposalAction,
)
from opencs.harness.audit_log import AuditLog
from opencs.memory.memory_store import MemoryStore
from opencs.replay.types import ReplayResult, Verdict


def _fake_replay_result(verdict: Verdict) -> ReplayResult:
    return ReplayResult(
        session_id="sess-e2e",
        verdict=verdict,
        divergence_points=[],
        replay_event_count=4,
        baseline_event_count=4,
    )


async def test_skill_fix_auto_promotes(tmp_path: Path) -> None:
    fake_engine = MagicMock()
    fake_engine.replay = AsyncMock(return_value=_fake_replay_result(Verdict.BADCASE_FIXED))

    audit_log = AuditLog(db_path=":memory:")
    gate = EvolutionGate(audit_log=audit_log)
    runner = ShadowRunner(engine=fake_engine)
    handler = SkillProposalHandler(skills_dir=str(tmp_path / "skills"))

    proposal = Proposal(
        id="e2e-skill-1",
        dimension=EvolutionDimension.SKILL,
        action=ProposalAction.UPDATE,
        payload={"skill_id": "refund_flow", "content": "# Refund\nProcess refunds promptly."},
        evidence={"badcase_conversation_id": "conv-badcase-1"},
        confidence=0.92,
        risk_level="low",
    )

    shadow_result = await runner.run(proposal)
    assert shadow_result.verdict == Verdict.BADCASE_FIXED
    assert shadow_result.blocks_gate is False

    decision = gate.evaluate(proposal)
    assert decision == GateDecision.AUTO_PROMOTE

    handler.apply(proposal)
    skill_file = tmp_path / "skills" / "refund_flow.md"
    assert skill_file.exists()
    assert "Process refunds promptly." in skill_file.read_text()

    entries = audit_log.recent(limit=10)
    assert any(e.actor == "evolution_gate" for e in entries)


async def test_memory_pii_hitl() -> None:
    audit_log = AuditLog(db_path=":memory:")
    gate = EvolutionGate(audit_log=audit_log)
    hitl_queue = EvolutionHITLQueue()
    memory_store = MemoryStore()
    handler = MemoryProposalHandler(l2_store=memory_store.l2)

    proposal = Proposal(
        id="e2e-mem-1",
        dimension=EvolutionDimension.MEMORY,
        action=ProposalAction.UPDATE,
        payload={
            "subject_id": "customer:u99",
            "kind": "customer_profile",
            "body": "VIP; preferred contact: mobile",
            "key": "phone_number",
        },
        confidence=0.88,
        risk_level="medium",
    )

    decision = gate.evaluate(proposal)
    assert decision == GateDecision.HITL_PENDING

    hitl_queue.enqueue(proposal, reason="PII field detected: phone_number")
    assert len(hitl_queue.pending()) == 1

    item = hitl_queue.approve("e2e-mem-1", reviewer="compliance_team")
    assert item.approved_by == "compliance_team"
    assert hitl_queue.pending() == []

    handler.apply(proposal)
    entries = memory_store.l2.get_by_subject("customer:u99")
    assert len(entries) == 1
    assert "VIP" in entries[0].body


async def test_inconclusive_shadow_blocks() -> None:
    fake_engine = MagicMock()
    fake_engine.replay = AsyncMock(return_value=_fake_replay_result(Verdict.INCONCLUSIVE))

    audit_log = AuditLog(db_path=":memory:")
    EvolutionGate(audit_log=audit_log)
    runner = ShadowRunner(engine=fake_engine)

    proposal = Proposal(
        id="e2e-shadow-inconclusive",
        dimension=EvolutionDimension.SKILL,
        action=ProposalAction.UPDATE,
        payload={"skill_id": "complex_skill", "content": "# Complex"},
        evidence={"badcase_conversation_id": "conv-ambiguous-1"},
        confidence=0.65,
        risk_level="medium",
    )

    shadow_result = await runner.run(proposal)
    assert shadow_result.verdict == Verdict.INCONCLUSIVE
    assert shadow_result.blocks_gate is True

    entries = audit_log.recent(limit=10)
    assert all(e.actor != "evolution_gate" for e in entries), (
        "EvolutionGate.evaluate() must not be called when ShadowRunner blocks"
    )
