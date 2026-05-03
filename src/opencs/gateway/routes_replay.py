from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from opencs.replay.types import ReplayMode, ReplayOverrides, ReplayScope, ReplaySession


class ReplayRequest(BaseModel):
    source_conversation_id: str
    mode: ReplayMode = ReplayMode.WHAT_IF
    scope: ReplayScope = ReplayScope.CONVERSATION
    overrides: ReplayOverrides = ReplayOverrides()
    badcase_event_index: int | None = None


class ReplayResponse(BaseModel):
    session_id: str
    verdict: str
    divergence_count: int
    baseline_event_count: int
    replay_event_count: int


router = APIRouter(tags=["replay"])


@router.post("/replays", response_model=ReplayResponse)
async def post_replay(req_body: ReplayRequest, request: Request) -> ReplayResponse:
    engine = getattr(request.app.state, "replay_engine", None)
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="ReplayEngine not configured. Pass replay_engine= to create_app().",
        )
    session = ReplaySession(
        source_conversation_id=req_body.source_conversation_id,
        mode=req_body.mode,
        scope=req_body.scope,
        overrides=req_body.overrides,
    )
    result = await engine.replay(session)
    return ReplayResponse(
        session_id=result.session_id,
        verdict=str(result.verdict),
        divergence_count=len(result.divergence_points),
        baseline_event_count=result.baseline_event_count,
        replay_event_count=result.replay_event_count,
    )
