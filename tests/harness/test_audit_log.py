from datetime import UTC, datetime

import pytest

from opencs.harness.action_plan import ActionPlan, RiskTier
from opencs.harness.audit_log import AuditEntry, AuditLog


def _plan(action_id: str = "act-1") -> ActionPlan:
    return ActionPlan(
        action_id=action_id,
        tool_id="crm.read_customer",
        args={"customer_id": "c1"},
        intent="test intent",
        risk_hint=RiskTier.GREEN,
    )


def test_append_and_read_back(tmp_path) -> None:
    log = AuditLog(db_path=str(tmp_path / "audit.db"))
    entry = AuditEntry(
        action_id="act-1",
        tool_id="crm.read_customer",
        risk_tier=RiskTier.GREEN,
        decision="auto_approved",
        actor="action_guard",
        ts=datetime(2026, 5, 1, tzinfo=UTC),
        note=None,
    )
    log.append(entry)
    rows = log.recent(limit=10)
    assert len(rows) == 1
    assert rows[0].action_id == "act-1"
    assert rows[0].decision == "auto_approved"


def test_append_multiple_ordered_by_ts(tmp_path) -> None:
    log = AuditLog(db_path=str(tmp_path / "audit.db"))
    for i in range(3):
        log.append(AuditEntry(
            action_id=f"act-{i}",
            tool_id="t",
            risk_tier=RiskTier.GREEN,
            decision="auto_approved",
            actor="ag",
            ts=datetime(2026, 5, 1, i + 1, tzinfo=UTC),
            note=None,
        ))
    rows = log.recent(limit=2)
    assert len(rows) == 2
    # most recent first
    assert rows[0].action_id == "act-2"
    assert rows[1].action_id == "act-1"


def test_in_memory_db() -> None:
    log = AuditLog(db_path=":memory:")
    log.append(AuditEntry(
        action_id="a",
        tool_id="t",
        risk_tier=RiskTier.YELLOW,
        decision="auto_approved",
        actor="ag",
        ts=datetime(2026, 5, 1, tzinfo=UTC),
        note="test note",
    ))
    rows = log.recent(limit=5)
    assert rows[0].note == "test note"
