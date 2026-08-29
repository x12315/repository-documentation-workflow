"""Fail-closed stdlib validation for this skill's supported frontmatter schema."""

from __future__ import annotations

import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
FRONTMATTER_LINE_RE = re.compile(r"([a-z-]+):[ \t]+(.+)")


def validate_skill_schema(skill_root: Path) -> None:
    """Validate the exact two-scalar frontmatter contract used by this release."""
    skill_file = skill_root / "SKILL.md"
    content = skill_file.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    closing = content.find("\n---", 4)
    if closing < 0:
        raise ValueError("SKILL.md frontmatter has no closing delimiter")
    frontmatter = content[4:closing]
    fields: dict[str, str] = {}
    for line_number, line in enumerate(frontmatter.splitlines(), 2):
        match = FRONTMATTER_LINE_RE.fullmatch(line)
        if match is None:
            raise ValueError(
                f"SKILL.md:{line_number}: unsupported YAML; frontmatter must use one-line scalar fields"
            )
        key, value = match.groups()
        if key in fields:
            raise ValueError(f"SKILL.md:{line_number}: duplicate frontmatter field: {key}")
        fields[key] = value.strip()
    if set(fields) != {"name", "description"}:
        raise ValueError("frontmatter must contain exactly name and description")
    name = fields["name"]
    if NAME_RE.fullmatch(name) is None or len(name) > 64:
        raise ValueError("name must be lowercase kebab-case with at most 64 characters")
    if name != skill_root.name:
        raise ValueError("name must match the skill directory")
    description = fields["description"]
    if not description or len(description) > 1024 or "<" in description or ">" in description:
        raise ValueError("description must be 1-1024 characters and contain no angle brackets")

    body = content[closing + 4 :]
    fence_marker = None
    fence_length = 0
    for line in body.splitlines():
        fence = re.match(r"^[ \t]*(?:(?:[-+*]|\d+[.)])[ \t]+)?(`{3,}|~{3,})(.*)$", line)
        if fence:
            marker = fence.group(1)
            if fence_marker is None:
                fence_marker = marker[0]
                fence_length = len(marker)
            elif marker[0] == fence_marker and len(marker) >= fence_length and not fence.group(2).strip():
                fence_marker = None
                fence_length = 0
            continue
        if fence_marker is None and re.fullmatch(r"[ ]{0,3}\[TODO:[^\n]*\][ \t]*", line):
            raise ValueError("Skill instructions contain an unfinished TODO placeholder")


def main() -> int:
    """Run strict schema validation for a supplied skill directory."""
    if len(sys.argv) != 2:
        print("usage: verify_skill_schema.py SKILL_ROOT", file=sys.stderr)
        return 2
    try:
        validate_skill_schema(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"skill schema verification failed: {error}", file=sys.stderr)
        return 1
    print("verified strict stdlib skill schema (name, description, body placeholders)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
