from unittest.mock import AsyncMock, MagicMock

import pytest

from opencs.evolution.shadow_runner import ShadowRunner
from opencs.evolution.types import EvolutionDimension, Proposal, ProposalAction
from opencs.replay.types import ReplayResult, Verdict


def _proposal(evidence: dict | None = None, payload: dict | None = None) -> Proposal:
    return Proposal(
        id="prop-shadow-1",
        dimension=EvolutionDimension.SKILL,
        action=ProposalAction.UPDATE,
        payload=payload or {"skill_id": "greet", "content": "# Greet"},
        evidence=evidence or {},
        confidence=0.9,
        risk_level="low",
    )


def _fake_replay_result(verdict: Verdict) -> ReplayResult:
    return ReplayResult(
        session_id="sess-test",
        verdict=verdict,
        divergence_points=[],
        replay_event_count=3,
        baseline_event_count=3,
    )


@pytest.fixture
def engine() -> MagicMock:
    return MagicMock()


@pytest.fixture
def runner(engine: MagicMock) -> ShadowRunner:
    return ShadowRunner(engine=engine)


async def test_no_badcase_id_skips_replay(runner: ShadowRunner, engine: MagicMock) -> None:
    result = await runner.run(_proposal(evidence={}))
    assert result.verdict is None
    assert result.blocks_gate is False
    engine.replay.assert_not_called()


async def test_badcase_fixed_does_not_block(runner: ShadowRunner, engine: MagicMock) -> None:
    engine.replay = AsyncMock(return_value=_fake_replay_result(Verdict.BADCASE_FIXED))
    result = await runner.run(_proposal(
        evidence={"badcase_conversation_id": "conv-bad-1"}
    ))
    assert result.verdict == Verdict.BADCASE_FIXED
    assert result.blocks_gate is False


async def test_inconclusive_blocks_gate(runner: ShadowRunner, engine: MagicMock) -> None:
    engine.replay = AsyncMock(return_value=_fake_replay_result(Verdict.INCONCLUSIVE))
    result = await runner.run(_proposal(
        evidence={"badcase_conversation_id": "conv-bad-2"}
    ))
    assert result.verdict == Verdict.INCONCLUSIVE
    assert result.blocks_gate is True


async def test_badcase_remains_does_not_block(runner: ShadowRunner, engine: MagicMock) -> None:
    engine.replay = AsyncMock(return_value=_fake_replay_result(Verdict.BADCASE_REMAINS))
    result = await runner.run(_proposal(
        evidence={"badcase_conversation_id": "conv-bad-3"}
    ))
    assert result.blocks_gate is False


async def test_prompt_override_forwarded(runner: ShadowRunner, engine: MagicMock) -> None:
    engine.replay = AsyncMock(return_value=_fake_replay_result(Verdict.BADCASE_FIXED))
    await runner.run(_proposal(
        evidence={"badcase_conversation_id": "conv-bad-4"},
        payload={"skill_id": "greet", "content": "x", "prompt_override": "Be strict."},
    ))
    call_args = engine.replay.call_args
    session = call_args[0][0] if call_args[0] else call_args[1]["session"]
    assert session.overrides.prompt_override == "Be strict."


async def test_result_contains_session_id(runner: ShadowRunner, engine: MagicMock) -> None:
    engine.replay = AsyncMock(return_value=_fake_replay_result(Verdict.BADCASE_FIXED))
    result = await runner.run(_proposal(
        evidence={"badcase_conversation_id": "conv-bad-5"}
    ))
    assert result.replay_session_id == "sess-test"
    assert result.proposal_id == "prop-shadow-1"
