from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from opencs.channel.registry import ChannelRegistry
from opencs.channel.webchat import WebChatAdapter
from opencs.gateway.app import create_app
from opencs.replay.types import ReplayResult, Verdict


def _fake_replay_result(verdict: Verdict = Verdict.BADCASE_FIXED) -> ReplayResult:
    return ReplayResult(
        session_id="sess-abc",
        verdict=verdict,
        divergence_points=[],
        replay_event_count=3,
        baseline_event_count=3,
    )


@pytest.fixture
def client() -> TestClient:
    registry = ChannelRegistry()
    registry.register(WebChatAdapter())
    fake_engine = MagicMock()
    fake_engine.replay = AsyncMock(return_value=_fake_replay_result())
    app = create_app(
        registry,
        webchat_handler=None,
        replay_engine=fake_engine,
    )
    return TestClient(app)


@pytest.fixture
def client_no_engine() -> TestClient:
    registry = ChannelRegistry()
    registry.register(WebChatAdapter())
    app = create_app(registry, webchat_handler=None)
    return TestClient(app)


def test_post_replay_returns_200(client: TestClient) -> None:
    resp = client.post(
        "/replays",
        json={
            "source_conversation_id": "conv-1",
            "mode": "what_if",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "sess-abc"
    assert data["verdict"] == "badcase_fixed"
    assert "divergence_count" in data
    assert "baseline_event_count" in data
    assert "replay_event_count" in data


def test_post_replay_with_overrides(client: TestClient) -> None:
    resp = client.post(
        "/replays",
        json={
            "source_conversation_id": "conv-2",
            "mode": "what_if",
            "overrides": {"prompt_override": "Be strict."},
        },
    )
    assert resp.status_code == 200


def test_post_replay_strict_mode(client: TestClient) -> None:
    resp = client.post(
        "/replays",
        json={
            "source_conversation_id": "conv-3",
            "mode": "strict",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "badcase_fixed"


def test_post_replay_503_when_no_engine(client_no_engine: TestClient) -> None:
    resp = client_no_engine.post(
        "/replays",
        json={"source_conversation_id": "conv-1", "mode": "what_if"},
    )
    assert resp.status_code == 503


def test_create_app_without_replay_engine_still_works(client_no_engine: TestClient) -> None:
    resp = client_no_engine.get("/health")
    assert resp.status_code == 200
