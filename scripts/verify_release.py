"""Verify that release Markdown depends only on files inside the skill directory."""

from __future__ import annotations

import re
import sys
from pathlib import Path


MARKDOWN_LINK_RE = re.compile(r"\[[^]]+\]\((?:<([^>]+)>|([^\s)#]+))(?:#[^)]+)?\)")


def verify_local_markdown_links(skill_root: Path) -> int:
    """Reject missing or out-of-package local targets in release Markdown."""
    skill_root = skill_root.resolve()
    checked = 0
    failures = []
    for markdown in skill_root.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        for angle_target, plain_target in MARKDOWN_LINK_RE.findall(text):
            target = angle_target or plain_target
            if "://" in target or target.startswith("mailto:"):
                continue
            resolved = (markdown.parent / target).resolve()
            try:
                resolved.relative_to(skill_root)
            except ValueError:
                failures.append(f"{markdown.relative_to(skill_root)} -> {target} leaves the release directory")
                continue
            if not resolved.exists():
                failures.append(f"{markdown.relative_to(skill_root)} -> {target} is missing")
                continue
            checked += 1
    if failures:
        raise ValueError("invalid local Markdown targets:\n- " + "\n- ".join(failures))
    return checked


def main() -> int:
    """Run release-boundary verification for a supplied skill directory."""
    if len(sys.argv) != 2:
        print("usage: verify_release.py SKILL_ROOT", file=sys.stderr)
        return 2
    try:
        checked = verify_local_markdown_links(Path(sys.argv[1]))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"release verification failed: {error}", file=sys.stderr)
        return 1
    print(f"verified {checked} in-package local Markdown targets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
