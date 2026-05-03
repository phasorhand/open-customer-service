from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field

_DDL = """
CREATE TABLE IF NOT EXISTS crm_config (
    id                  INTEGER PRIMARY KEY CHECK (id = 1),
    base_url            TEXT NOT NULL,
    schema_json         TEXT NOT NULL,
    exposed_operations  TEXT NOT NULL DEFAULT '[]',
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


@dataclass
class CRMConfig:
    base_url: str
    schema_json: str
    exposed_operations: list[str] = field(default_factory=list)


class CRMConfigStore:
    """Single-row config table. Stores the current CRM integration settings."""

    def __init__(self, db_path: str = "evolution.db") -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(_DDL)
        self._conn.commit()

    def save(self, cfg: CRMConfig) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO crm_config "
            "(id, base_url, schema_json, exposed_operations, updated_at) "
            "VALUES (1, ?, ?, ?, datetime('now'))",
            (cfg.base_url, cfg.schema_json, json.dumps(cfg.exposed_operations)),
        )
        self._conn.commit()

    def get(self) -> CRMConfig | None:
        cur = self._conn.execute(
            "SELECT base_url, schema_json, exposed_operations FROM crm_config WHERE id=1"
        )
        row = cur.fetchone()
        if row is None:
            return None
        base_url, schema_json, ops_json = row
        return CRMConfig(
            base_url=base_url,
            schema_json=schema_json,
            exposed_operations=json.loads(ops_json),
        )
