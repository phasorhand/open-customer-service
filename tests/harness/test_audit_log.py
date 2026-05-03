from datetime import UTC, datetime

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


def test_audit_log_list_filters_by_actor() -> None:
    from datetime import datetime, timedelta
    from opencs.harness.action_plan import RiskTier
    from opencs.harness.audit_log import AuditEntry, AuditLog

    log = AuditLog(db_path=":memory:")
    t0 = datetime(2026, 5, 1, 12, 0, 0)
    for i, actor in enumerate(["action_guard", "alice", "action_guard"]):
        log.append(AuditEntry(
            action_id=f"a-{i}", tool_id="t", risk_tier=RiskTier.GREEN,
            decision="auto_approved", actor=actor,
            ts=t0 + timedelta(seconds=i), note=None,
        ))
    alice_entries = log.list(actor="alice")
    assert len(alice_entries) == 1
    assert alice_entries[0].actor == "alice"
    guard_entries = log.list(actor="action_guard")
    assert len(guard_entries) == 2


def test_audit_log_list_pagination() -> None:
    from datetime import datetime, timedelta
    from opencs.harness.action_plan import RiskTier
    from opencs.harness.audit_log import AuditEntry, AuditLog

    log = AuditLog(db_path=":memory:")
    t0 = datetime(2026, 5, 1, 12, 0, 0)
    for i in range(5):
        log.append(AuditEntry(
            action_id=f"a-{i}", tool_id="t", risk_tier=RiskTier.GREEN,
            decision="auto_approved", actor="x",
            ts=t0 + timedelta(seconds=i), note=None,
        ))
    page1 = log.list(limit=2, offset=0)
    page2 = log.list(limit=2, offset=2)
    assert len(page1) == 2
    assert len(page2) == 2
    assert page1[0].action_id != page2[0].action_id
