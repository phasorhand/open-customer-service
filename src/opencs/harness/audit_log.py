import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from opencs.harness.action_plan import RiskTier


@dataclass
class AuditEntry:
    action_id: str
    tool_id: str
    risk_tier: RiskTier
    decision: str          # "auto_approved" | "hitl_queued" | "rejected"
    actor: str             # "action_guard" | "<reviewer_id>"
    ts: datetime
    note: str | None


_DDL = """
CREATE TABLE IF NOT EXISTS audit_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id TEXT NOT NULL,
    tool_id   TEXT NOT NULL,
    risk_tier INTEGER NOT NULL,
    decision  TEXT NOT NULL,
    actor     TEXT NOT NULL,
    ts        TEXT NOT NULL,
    note      TEXT
)
"""


class AuditLog:
    """Append-only SQLite audit store. Thread-safe via check_same_thread=False."""

    def __init__(self, db_path: str = "audit.db") -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(_DDL)
        self._conn.commit()

    def append(self, entry: AuditEntry) -> None:
        self._conn.execute(
            "INSERT INTO audit_log "
            "(action_id, tool_id, risk_tier, decision, actor, ts, note) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                entry.action_id,
                entry.tool_id,
                int(entry.risk_tier),
                entry.decision,
                entry.actor,
                entry.ts.isoformat(),
                entry.note,
            ),
        )
        self._conn.commit()

    def recent(self, *, limit: int = 100) -> list[AuditEntry]:
        cur = self._conn.execute(
            "SELECT action_id, tool_id, risk_tier, decision, actor, ts, note "
            "FROM audit_log ORDER BY ts DESC LIMIT ?",
            (limit,),
        )
        rows = []
        for row in cur.fetchall():
            action_id, tool_id, risk_tier, decision, actor, ts_str, note = row
            rows.append(AuditEntry(
                action_id=action_id,
                tool_id=tool_id,
                risk_tier=RiskTier(risk_tier),
                decision=decision,
                actor=actor,
                ts=datetime.fromisoformat(ts_str),
                note=note,
            ))
        return rows
