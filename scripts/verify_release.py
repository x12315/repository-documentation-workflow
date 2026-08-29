"""Verify that release Markdown depends only on files inside the skill directory."""

from __future__ import annotations

import re
import sys
from pathlib import Path


MARKDOWN_LINK_RE = re.compile(r"\[[^]]+\]\((?:<([^>]+)>|([^\s)#]+))(?:#[^)]+)?\)")


def _verify_local_markdown_links(markdown_files: list[Path], boundary_root: Path) -> int:
    """Reject missing or boundary-crossing local targets from Markdown files."""
    boundary_root = boundary_root.resolve()
    checked = 0
    failures = []
    for markdown in markdown_files:
        text = markdown.read_text(encoding="utf-8")
        for angle_target, plain_target in MARKDOWN_LINK_RE.findall(text):
            target = angle_target or plain_target
            if "://" in target or target.startswith("mailto:"):
                continue
            resolved = (markdown.parent / target).resolve()
            try:
                resolved.relative_to(boundary_root)
            except ValueError:
                failures.append(f"{markdown.relative_to(boundary_root)} -> {target} leaves the release directory")
                continue
            if not resolved.exists():
                failures.append(f"{markdown.relative_to(boundary_root)} -> {target} is missing")
                continue
            checked += 1
    if failures:
        raise ValueError("invalid local Markdown targets:\n- " + "\n- ".join(failures))
    return checked


def verify_local_markdown_links(skill_root: Path) -> int:
    """Reject missing or out-of-package local targets in release Markdown."""
    skill_root = skill_root.resolve()
    return _verify_local_markdown_links(list(skill_root.rglob("*.md")), skill_root)


def verify_repository_markdown_links(repository_root: Path) -> int:
    """Verify repository Markdown links without reading Git metadata or scratch trees."""
    repository_root = repository_root.resolve()
    excluded_roots = {".git", ".superpowers"}
    markdown_files = [
        path
        for path in repository_root.rglob("*.md")
        if not (path.relative_to(repository_root).parts and path.relative_to(repository_root).parts[0] in excluded_roots)
    ]
    return _verify_local_markdown_links(markdown_files, repository_root)


def main() -> int:
    """Run release-boundary verification for a supplied skill directory."""
    arguments = sys.argv[1:]
    if len(arguments) == 1:
        root = Path(arguments[0])
        verifier = verify_local_markdown_links
        success_message = "in-package"
    elif len(arguments) == 2 and arguments[0] == "--repository-root":
        root = Path(arguments[1])
        verifier = verify_repository_markdown_links
        success_message = "repository-root"
    else:
        print("usage: verify_release.py SKILL_ROOT | --repository-root REPOSITORY_ROOT", file=sys.stderr)
        return 2
    try:
        checked = verifier(root)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"release verification failed: {error}", file=sys.stderr)
        return 1
    print(f"verified {checked} {success_message} local Markdown targets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
