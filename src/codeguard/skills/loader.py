from __future__ import annotations
import re
from pathlib import Path
from codeguard.models.entities import Skill


class SkillLoader:
    def __init__(self, skills_dir: Path):
        self._dir = skills_dir

    def load(self) -> list[Skill]:
        if not self._dir.exists():
            return []
        skills = []
        for f in self._dir.glob("*.md"):
            try:
                skill = self._parse_file(f)
                if skill:
                    skills.append(skill)
            except Exception:
                continue
        return skills

    def _parse_file(self, path: Path) -> Skill | None:
        content = path.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
        if not match:
            return None
        frontmatter = match.group(1)
        instructions = match.group(2).strip()
        name = self._extract(frontmatter, "name")
        trigger = self._extract(frontmatter, "trigger")
        if not name:
            return None
        return Skill(name=name, trigger=trigger, instructions=instructions, file_path=str(path))

    def _extract(self, text: str, key: str) -> str:
        match = re.search(rf"^{key}:\s*(.+)$", text, re.MULTILINE)
        return match.group(1).strip() if match else ""

    def match(self, context: str) -> list[Skill]:
        skills = self.load()
        matched = []
        context_lower = context.lower()
        for skill in skills:
            triggers = [t.strip().lower() for t in skill.trigger.split(",")]
            if any(t in context_lower for t in triggers):
                matched.append(skill)
        return matched
