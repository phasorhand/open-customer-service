import sqlite3
from dataclasses import dataclass
from datetime import datetime

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

    def list(
        self,
        *,
        actor: str | None = None,
        decision: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEntry]:
        clauses: list[str] = []
        params: list[object] = []
        if actor is not None:
            clauses.append("actor=?")
            params.append(actor)
        if decision is not None:
            clauses.append("decision=?")
            params.append(decision)
        if since is not None:
            clauses.append("ts >= ?")
            params.append(since.isoformat())
        if until is not None:
            clauses.append("ts <= ?")
            params.append(until.isoformat())
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([limit, offset])
        cur = self._conn.execute(
            "SELECT action_id, tool_id, risk_tier, decision, actor, ts, note "
            f"FROM audit_log {where} ORDER BY id DESC LIMIT ? OFFSET ?",
            tuple(params),
        )
        result = []
        for row in cur.fetchall():
            action_id, tool_id, risk_tier, decision_v, actor_v, ts_str, note = row
            result.append(AuditEntry(
                action_id=action_id,
                tool_id=tool_id,
                risk_tier=RiskTier(risk_tier),
                decision=decision_v,
                actor=actor_v,
                ts=datetime.fromisoformat(ts_str),
                note=note,
            ))
        return result

    def count(
        self,
        *,
        actor: str | None = None,
        decision: str | None = None,
    ) -> int:
        clauses: list[str] = []
        params: list[object] = []
        if actor is not None:
            clauses.append("actor=?")
            params.append(actor)
        if decision is not None:
            clauses.append("decision=?")
            params.append(decision)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        cur = self._conn.execute(
            f"SELECT COUNT(*) FROM audit_log {where}",
            tuple(params),
        )
        return int(cur.fetchone()[0])
