from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from opencs.replay.types import (
    ReplayMode,
    ReplayOverrides,
    ReplayScope,
    ReplaySession,
    Verdict,
)

if TYPE_CHECKING:
    from opencs.evolution.types import Proposal
    from opencs.replay.engine import ReplayEngine
    from opencs.replay.types import ReplayResult


@dataclass
class ShadowResult:
    proposal_id: str
    verdict: Verdict | None
    replay_session_id: str | None

    @property
    def blocks_gate(self) -> bool:
        return self.verdict == Verdict.INCONCLUSIVE


class ShadowRunner:
    def __init__(self, *, engine: ReplayEngine) -> None:
        self._engine = engine

    async def run(self, proposal: Proposal) -> ShadowResult:
        conversation_id = proposal.evidence.get("badcase_conversation_id")
        if not conversation_id:
            return ShadowResult(
                proposal_id=proposal.id,
                verdict=None,
                replay_session_id=None,
            )

        overrides = ReplayOverrides(
            prompt_override=proposal.payload.get("prompt_override"),
            skill_override=proposal.payload.get("skill_override"),
            model_override=proposal.payload.get("model_override"),
        )
        session = ReplaySession(
            source_conversation_id=str(conversation_id),
            mode=ReplayMode.WHAT_IF,
            scope=ReplayScope.CONVERSATION,
            overrides=overrides,
        )
        result: ReplayResult = await self._engine.replay(session)
        return ShadowResult(
            proposal_id=proposal.id,
            verdict=result.verdict,
            replay_session_id=result.session_id,
        )
