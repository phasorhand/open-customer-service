from __future__ import annotations

import json
import sqlite3
from typing import Any

from opencs.evolution.types import (
    EvolutionDimension,
    GateDecision,
    Proposal,
    ProposalAction,
    ProposalStatus,
)

_DDL = """
CREATE TABLE IF NOT EXISTS proposals (
    id               TEXT PRIMARY KEY,
    dimension        TEXT NOT NULL,
    action           TEXT NOT NULL,
    payload          TEXT NOT NULL,
    evidence         TEXT NOT NULL DEFAULT '{}',
    confidence       REAL NOT NULL,
    risk_level       TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'pending',
    replay_result    TEXT,
    gate_decision    TEXT,
    reviewer         TEXT,
    rejection_note   TEXT
)
"""


class ProposalStore:
    def __init__(self, db_path: str = "evolution.db") -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(_DDL)
        self._conn.commit()

    def save(self, proposal: Proposal) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO proposals "
            "(id, dimension, action, payload, evidence, confidence, risk_level, "
            " status, replay_result, gate_decision, reviewer, rejection_note) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                proposal.id,
                str(proposal.dimension),
                str(proposal.action),
                json.dumps(proposal.payload),
                json.dumps(proposal.evidence),
                proposal.confidence,
                proposal.risk_level,
                str(proposal.status),
                json.dumps(proposal.replay_result) if proposal.replay_result is not None else None,
                str(proposal.gate_decision) if proposal.gate_decision is not None else None,
                proposal.reviewer,
                proposal.rejection_note,
            ),
        )
        self._conn.commit()

    def get(self, proposal_id: str) -> Proposal | None:
        cur = self._conn.execute(
            "SELECT id, dimension, action, payload, evidence, confidence, risk_level, "
            "status, replay_result, gate_decision, reviewer, rejection_note "
            "FROM proposals WHERE id=?",
            (proposal_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_proposal(row)

    def update_status(self, proposal_id: str, status: ProposalStatus) -> None:
        self._conn.execute(
            "UPDATE proposals SET status=? WHERE id=?",
            (str(status), proposal_id),
        )
        self._conn.commit()

    def update_gate_decision(
        self,
        proposal_id: str,
        *,
        gate_decision: GateDecision,
        status: ProposalStatus,
        reviewer: str | None = None,
        rejection_note: str | None = None,
    ) -> None:
        self._conn.execute(
            "UPDATE proposals SET gate_decision=?, status=?, reviewer=?, "
            "rejection_note=? WHERE id=?",
            (str(gate_decision), str(status), reviewer, rejection_note, proposal_id),
        )
        self._conn.commit()

    def attach_replay_result(self, proposal_id: str, result_dict: dict[str, Any]) -> None:
        self._conn.execute(
            "UPDATE proposals SET replay_result=? WHERE id=?",
            (json.dumps(result_dict), proposal_id),
        )
        self._conn.commit()

    def list_by_status(self, status: ProposalStatus) -> list[Proposal]:
        cur = self._conn.execute(
            "SELECT id, dimension, action, payload, evidence, confidence, risk_level, "
            "status, replay_result, gate_decision, reviewer, rejection_note "
            "FROM proposals WHERE status=? ORDER BY rowid ASC",
            (str(status),),
        )
        return [self._row_to_proposal(row) for row in cur.fetchall()]

    @staticmethod
    def _row_to_proposal(row: tuple[Any, ...]) -> Proposal:
        (
            pid, dimension, action, payload_json, evidence_json, confidence,
            risk_level, status, replay_result_json, gate_decision, reviewer, rejection_note,
        ) = row
        return Proposal(
            id=pid,
            dimension=EvolutionDimension(dimension),
            action=ProposalAction(action),
            payload=json.loads(payload_json),
            evidence=json.loads(evidence_json),
            confidence=confidence,
            risk_level=risk_level,
            status=ProposalStatus(status),
            replay_result=(
                json.loads(replay_result_json) if replay_result_json is not None else None
            ),
            gate_decision=GateDecision(gate_decision) if gate_decision is not None else None,
            reviewer=reviewer,
            rejection_note=rejection_note,
        )
