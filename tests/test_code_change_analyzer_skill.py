"""Tests for the Code Change Analyzer Skill.

Validates that:
- The skill file exists at .opencode/skills/code-change-analyzer/SKILL.md
- YAML frontmatter contains valid name and description
- Contains the 10-step deterministic analysis workflow
- Defines confidence standards ([Confirmed], [Likely], [Unknown])
- Answers the required core questions without conflating Git states
"""

import os
from pathlib import Path


def test_skill_file_exists():
    """Skill must exist at .opencode/skills/code-change-analyzer/SKILL.md."""
    repo_root = Path(__file__).parent.parent
    skill_file = repo_root / ".opencode" / "skills" / "code-change-analyzer" / "SKILL.md"

    assert skill_file.is_file(), f"Skill file not found at {skill_file}"


def test_skill_yaml_frontmatter():
    """Skill must have valid YAML frontmatter with name and description."""
    repo_root = Path(__file__).parent.parent
    skill_file = repo_root / ".opencode" / "skills" / "code-change-analyzer" / "SKILL.md"

    content = skill_file.read_text(encoding="utf-8")
    assert content.startswith("---"), "Skill must start with YAML frontmatter delimiters"

    parts = content.split("---")
    assert len(parts) >= 3, "Frontmatter not properly closed with ---"

    frontmatter = parts[1]
    assert "name: code-change-analyzer" in frontmatter
    assert "description:" in frontmatter


def test_skill_required_sections_and_standards():
    """Skill must contain core questions, confidence labels, and 10-step workflow."""
    repo_root = Path(__file__).parent.parent
    skill_file = repo_root / ".opencode" / "skills" / "code-change-analyzer" / "SKILL.md"

    content = skill_file.read_text(encoding="utf-8")

    # Confidence standards
    assert "[Confirmed]" in content
    assert "[Likely]" in content
    assert "[Unknown]" in content

    # 10-step workflow
    for step_num in range(1, 11):
        assert f"Step {step_num}:" in content or f"Step {step_num} " in content

    # Key questions and rules
    assert "What changed in the code?" in content
    assert "git status" in content
    assert "git diff" in content
    assert "AST" in content
    assert "regressions" in content
    assert "Never modify source code" in content
