from __future__ import annotations

from pathlib import Path

from opencs.evolution.types import Proposal, ProposalAction


class SkillApplyError(Exception):
    pass


class SkillProposalHandler:
    def __init__(self, *, skills_dir: str) -> None:
        self._skills_dir = Path(skills_dir)

    def apply(self, proposal: Proposal) -> None:
        skill_id = proposal.payload.get("skill_id")
        if not skill_id:
            raise SkillApplyError("proposal.payload must contain 'skill_id'")

        skill_path = self._skills_dir / f"{skill_id}.md"

        if proposal.action in (ProposalAction.CREATE, ProposalAction.UPDATE):
            content = proposal.payload.get("content", "")
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text(str(content), encoding="utf-8")

        elif proposal.action == ProposalAction.DEPRECATE:
            if skill_path.exists():
                skill_path.unlink()
