import pytest
from pathlib import Path
from codeguard.skills.loader import SkillLoader


def test_load_skills_from_dir(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "tdd.md").write_text(
        "---\nname: tdd\ntrigger: test,tdd\n---\nWrite test first\n"
    )
    loader = SkillLoader(skills_dir)
    skills = loader.load()
    assert len(skills) == 1
    assert skills[0].name == "tdd"


def test_match_skills(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "tdd.md").write_text(
        "---\nname: tdd\ntrigger: test,tdd,red-green\n---\nWrite test first\n"
    )
    (skills_dir / "deploy.md").write_text(
        "---\nname: deploy\ntrigger: deploy,release\n---\nDeploy steps\n"
    )
    loader = SkillLoader(skills_dir)
    matched = loader.match("write a test for sorting")
    assert len(matched) == 1
    assert matched[0].name == "tdd"


def test_empty_dir(tmp_path: Path):
    loader = SkillLoader(tmp_path / "nonexistent")
    skills = loader.load()
    assert skills == []


def test_malformed_skill_skipped(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "bad.md").write_text("No frontmatter here")
    (skills_dir / "good.md").write_text(
        "---\nname: good\ntrigger: test\n---\nGood skill\n"
    )
    loader = SkillLoader(skills_dir)
    skills = loader.load()
    assert len(skills) == 1
    assert skills[0].name == "good"
