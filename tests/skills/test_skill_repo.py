from pathlib import Path

from opencs.skills.skill_repo import SkillRepo


def _make_skill(tmp_path: Path, name: str, keywords: list[str], body: str) -> None:
    skill_dir = tmp_path / name
    skill_dir.mkdir()
    keywords_yaml = "\n".join(f"  - {kw}" for kw in keywords)
    content = (
        f"---\nname: {name}\ndescription: Test skill\n"
        f"keywords:\n{keywords_yaml}\n---\n{body}\n"
    )
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")


def test_match_returns_body_for_keyword_hit(tmp_path) -> None:
    _make_skill(tmp_path, "greeting", ["hello", "hi"], "Greet warmly.")
    repo = SkillRepo(skills_dir=str(tmp_path))
    matches = repo.match("hello there")
    assert matches == ["Greet warmly."]


def test_match_case_insensitive(tmp_path) -> None:
    _make_skill(tmp_path, "refund", ["refund"], "Handle refund carefully.")
    repo = SkillRepo(skills_dir=str(tmp_path))
    assert repo.match("I want a REFUND") == ["Handle refund carefully."]


def test_match_no_hit_returns_empty(tmp_path) -> None:
    _make_skill(tmp_path, "greeting", ["hello"], "Greet warmly.")
    repo = SkillRepo(skills_dir=str(tmp_path))
    assert repo.match("tell me about shipping") == []


def test_match_multiple_skills(tmp_path) -> None:
    _make_skill(tmp_path, "s1", ["alpha"], "Skill one.")
    _make_skill(tmp_path, "s2", ["beta"], "Skill two.")
    repo = SkillRepo(skills_dir=str(tmp_path))
    assert repo.match("alpha test") == ["Skill one."]


def test_match_multiple_skills_hit(tmp_path) -> None:
    _make_skill(tmp_path, "s1", ["alpha"], "Skill one.")
    _make_skill(tmp_path, "s2", ["alpha"], "Skill two.")
    repo = SkillRepo(skills_dir=str(tmp_path))
    results = repo.match("alpha test")
    assert len(results) == 2
    assert "Skill one." in results
    assert "Skill two." in results


def test_empty_skills_dir(tmp_path) -> None:
    repo = SkillRepo(skills_dir=str(tmp_path))
    assert repo.match("anything") == []


def test_bundled_skills_dir_loads_without_error() -> None:
    bundled_dir = Path(__file__).parent.parent.parent / "src" / "opencs" / "skills" / "bundled"
    repo = SkillRepo(skills_dir=str(bundled_dir))
    matches = repo.match("hello")
    assert len(matches) >= 1
    matches2 = repo.match("refund")
    assert len(matches2) >= 1
