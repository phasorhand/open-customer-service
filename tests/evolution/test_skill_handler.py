import pytest
from pathlib import Path

from opencs.evolution.handlers.skill import SkillApplyError, SkillProposalHandler
from opencs.evolution.types import EvolutionDimension, Proposal, ProposalAction


def _skill_proposal(action: ProposalAction, skill_id: str = "greet", content: str = "# Greet\nSay hello.") -> Proposal:
    payload: dict = {"skill_id": skill_id, "content": content}
    return Proposal(
        id="prop-skill-1",
        dimension=EvolutionDimension.SKILL,
        action=action,
        payload=payload,
        confidence=0.9,
        risk_level="low",
    )


@pytest.fixture
def skills_dir(tmp_path: Path) -> Path:
    return tmp_path / "skills"


@pytest.fixture
def handler(skills_dir: Path) -> SkillProposalHandler:
    return SkillProposalHandler(skills_dir=str(skills_dir))


def test_create_writes_skill_file(handler: SkillProposalHandler, skills_dir: Path) -> None:
    handler.apply(_skill_proposal(ProposalAction.CREATE))
    skill_file = skills_dir / "greet.md"
    assert skill_file.exists()
    assert "Say hello." in skill_file.read_text()


def test_update_overwrites_skill_file(handler: SkillProposalHandler, skills_dir: Path) -> None:
    handler.apply(_skill_proposal(ProposalAction.CREATE, content="# Greet\nOld content."))
    handler.apply(_skill_proposal(ProposalAction.UPDATE, content="# Greet\nNew content."))
    assert "New content." in (skills_dir / "greet.md").read_text()
    assert "Old content." not in (skills_dir / "greet.md").read_text()


def test_deprecate_removes_skill_file(handler: SkillProposalHandler, skills_dir: Path) -> None:
    handler.apply(_skill_proposal(ProposalAction.CREATE))
    handler.apply(_skill_proposal(ProposalAction.DEPRECATE))
    assert not (skills_dir / "greet.md").exists()


def test_deprecate_is_idempotent_if_file_missing(handler: SkillProposalHandler) -> None:
    handler.apply(_skill_proposal(ProposalAction.DEPRECATE))


def test_missing_skill_id_raises(handler: SkillProposalHandler) -> None:
    bad = Proposal(
        id="prop-bad",
        dimension=EvolutionDimension.SKILL,
        action=ProposalAction.CREATE,
        payload={"content": "# No id"},
        confidence=0.9,
        risk_level="low",
    )
    with pytest.raises(SkillApplyError, match="skill_id"):
        handler.apply(bad)


def test_creates_parent_directory(handler: SkillProposalHandler, skills_dir: Path) -> None:
    sub = Proposal(
        id="prop-sub",
        dimension=EvolutionDimension.SKILL,
        action=ProposalAction.CREATE,
        payload={"skill_id": "greet", "content": "# Greet"},
        confidence=0.9,
        risk_level="low",
    )
    handler.apply(sub)
    assert (skills_dir / "greet.md").exists()
