import sqlite3
import uuid
from dataclasses import dataclass, field


@dataclass
class MemoryEntry:
    subject_id: str            # "customer:<id>" | "product:<id>" | "global"
    kind: str                  # "customer_profile" | "note" | "product_kb"
    body: str
    version_id: str = field(default="")  # set by store on write; empty means "not yet written"


_DDL = """
CREATE TABLE IF NOT EXISTS l2_memory (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id  TEXT NOT NULL,
    subject_id  TEXT NOT NULL,
    kind        TEXT NOT NULL,
    body        TEXT NOT NULL
)
"""
_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS l2_fts
USING fts5(body, content='l2_memory', content_rowid='id')
"""
_TRIGGER_INSERT = """
CREATE TRIGGER IF NOT EXISTS l2_ai AFTER INSERT ON l2_memory BEGIN
    INSERT INTO l2_fts(rowid, body) VALUES (new.id, new.body);
END
"""


class L2MemoryStore:
    """Long-term memory with FTS5 keyword search. All writes are versioned (append-only CoW)."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(_DDL)
        self._conn.execute(_FTS)
        self._conn.execute(_TRIGGER_INSERT)
        self._conn.commit()

    def write(self, entry: MemoryEntry) -> str:
        version_id = uuid.uuid4().hex
        self._conn.execute(
            "INSERT INTO l2_memory (version_id, subject_id, kind, body) VALUES (?,?,?,?)",
            (version_id, entry.subject_id, entry.kind, entry.body),
        )
        self._conn.commit()
        return version_id

    def search(self, query: str, *, limit: int = 10) -> list[MemoryEntry]:
        # Wrap query in double-quotes so FTS5 treats the whole string as a
        # phrase / literal token — prevents hyphens being parsed as NOT operator.
        fts_query = '"{}"'.format(query.replace('"', '""'))
        cur = self._conn.execute(
            "SELECT m.version_id, m.subject_id, m.kind, m.body "
            "FROM l2_memory m "
            "JOIN l2_fts ON l2_fts.rowid = m.id "
            "WHERE l2_fts MATCH ? "
            "ORDER BY rank "
            "LIMIT ?",
            (fts_query, limit),
        )
        return [
            MemoryEntry(version_id=r[0], subject_id=r[1], kind=r[2], body=r[3])
            for r in cur.fetchall()
        ]

    def get_by_subject(self, subject_id: str) -> list[MemoryEntry]:
        cur = self._conn.execute(
            "SELECT version_id, subject_id, kind, body FROM l2_memory "
            "WHERE subject_id=? ORDER BY id ASC",
            (subject_id,),
        )
        return [
            MemoryEntry(version_id=r[0], subject_id=r[1], kind=r[2], body=r[3])
            for r in cur.fetchall()
        ]
