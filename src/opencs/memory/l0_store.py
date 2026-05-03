from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime


@dataclass
class L0Event:
    conversation_id: str
    kind: str           # "inbound_message" | "action_guard_decision" | "worker_output"
    payload: dict[str, object]
    ts: datetime


_DDL = """
CREATE TABLE IF NOT EXISTS l0_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    kind            TEXT NOT NULL,
    payload_json    TEXT NOT NULL,
    ts              TEXT NOT NULL
)
"""
_IDX = "CREATE INDEX IF NOT EXISTS l0_conv_ts ON l0_events (conversation_id, ts)"


class L0RawEventStore:
    """Append-only raw event log. Never updated or deleted — source of truth for Replay."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(_DDL)
        self._conn.execute(_IDX)
        self._conn.commit()

    def append(self, event: L0Event) -> None:
        self._conn.execute(
            "INSERT INTO l0_events (conversation_id, kind, payload_json, ts) VALUES (?,?,?,?)",
            (
                event.conversation_id,
                event.kind,
                json.dumps(event.payload, ensure_ascii=False),
                event.ts.isoformat(),
            ),
        )
        self._conn.commit()

    def list(self, *, conversation_id: str, limit: int = 1000) -> list[L0Event]:
        cur = self._conn.execute(
            "SELECT conversation_id, kind, payload_json, ts "
            "FROM l0_events WHERE conversation_id=? ORDER BY ts ASC LIMIT ?",
            (conversation_id, limit),
        )
        rows = []
        for conv_id, kind, payload_json, ts_str in cur.fetchall():
            rows.append(L0Event(
                conversation_id=conv_id,
                kind=kind,
                payload=json.loads(payload_json),
                ts=datetime.fromisoformat(ts_str),
            ))
        return rows

    def list_by_kinds(
        self, *, conversation_id: str, kinds: list[str], limit: int = 1000
    ) -> list[L0Event]:
        placeholders = ",".join("?" for _ in kinds)
        cur = self._conn.execute(
            f"SELECT conversation_id, kind, payload_json, ts "
            f"FROM l0_events WHERE conversation_id=? AND kind IN ({placeholders}) "
            f"ORDER BY ts ASC LIMIT ?",
            (conversation_id, *kinds, limit),
        )
        rows = []
        for conv_id, kind, payload_json, ts_str in cur.fetchall():
            rows.append(L0Event(
                conversation_id=conv_id,
                kind=kind,
                payload=json.loads(payload_json),
                ts=datetime.fromisoformat(ts_str),
            ))
        return rows
