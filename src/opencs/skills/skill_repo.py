from pathlib import Path

import frontmatter


class SkillRepo:
    """Loads bundled SKILL.md files and matches them by keyword to customer messages."""

    def __init__(self, skills_dir: str) -> None:
        self._skills: list[tuple[list[str], str]] = []
        self._load(Path(skills_dir))

    def _load(self, root: Path) -> None:
        for skill_md in sorted(root.rglob("SKILL.md")):
            post = frontmatter.load(str(skill_md))
            keywords: list[str] = [str(k) for k in (post.get("keywords") or [])]
            body = post.content.strip()
            if keywords and body:
                self._skills.append((keywords, body))

    def match(self, text: str) -> list[str]:
        lower = text.lower()
        return [
            body
            for keywords, body in self._skills
            if any(kw.lower() in lower for kw in keywords)
        ]
