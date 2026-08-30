#!/usr/bin/env python3
"""Negative regression tests for deterministic verification boundaries."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from upstream_lock import validate_lock  # noqa: E402
from verify_release import (  # noqa: E402
    verify_local_markdown_links,
    verify_repository_markdown_links,
)
from verify_skill_schema import validate_skill_schema  # noqa: E402
from verify_tracked import verify_tracked_delivery  # noqa: E402


def initialize_delivery_repository(repository_root: Path) -> None:
    """Create a staged repository with an ignored Superpowers process file."""
    root_delivery_files = (
        ".gitignore",
        "LICENSE",
        "README.md",
        "CHANGELOG.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
    )
    for relative_name in root_delivery_files:
        path = repository_root / relative_name
        path.write_text("delivery\n", encoding="utf-8")
    (repository_root / ".gitignore").write_text(
        "docs/superpowers/\n",
        encoding="utf-8",
    )
    (repository_root / "docs").mkdir()
    (repository_root / "docs/guide.md").write_text("guide\n", encoding="utf-8")
    process_file = repository_root / "docs/superpowers/process.md"
    process_file.parent.mkdir()
    process_file.write_text("process\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repository_root, check=True)
    subprocess.run(
        ["git", "add", *root_delivery_files, "docs/guide.md"],
        cwd=repository_root,
        check=True,
    )


class VerificationBoundaryTest(unittest.TestCase):
    def test_tracked_delivery_excludes_repository_ignored_worktree_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            repository_root = Path(temp_name)
            initialize_delivery_repository(repository_root)
            self.assertEqual(8, verify_tracked_delivery(repository_root))

    def test_tracked_delivery_rejects_force_added_ignored_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            repository_root = Path(temp_name)
            initialize_delivery_repository(repository_root)
            subprocess.run(
                ["git", "add", "--force", "docs/superpowers/process.md"],
                cwd=repository_root,
                check=True,
            )
            with self.assertRaisesRegex(
                ValueError,
                "tracked files match repository ignore rules: docs/superpowers/process.md",
            ):
                verify_tracked_delivery(repository_root)

    def test_unlocked_upstream_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            skill_root = Path(temp_name)
            locked = skill_root / "references/upstream/example/SOURCE.md"
            locked.parent.mkdir(parents=True)
            locked.write_text("locked", encoding="utf-8")
            extra = skill_root / "references/upstream/example/EXTRA.md"
            extra.write_text("unlocked", encoding="utf-8")
            lock = {
                "version": 1,
                "updated_at": "2026-08-29",
                "sources": [{
                    "id": "example",
                    "repository": "https://github.com/example/example",
                    "commit": "a" * 40,
                    "license": "Public Domain",
                    "files": [{
                        "upstream_path": "SOURCE.md",
                        "vendored_path": "references/upstream/example/SOURCE.md",
                        "sha256": "b" * 64,
                    }],
                }],
            }
            with self.assertRaisesRegex(ValueError, "unlocked vendored files"):
                validate_lock(lock, skill_root)

    def test_markdown_link_outside_release_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            skill_root = root / "skill"
            skill_root.mkdir()
            (root / "outside.md").write_text("outside", encoding="utf-8")
            (skill_root / "SKILL.md").write_text("[escape](../outside.md)\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "leaves the release directory"):
                verify_local_markdown_links(skill_root)

    def test_repository_markdown_links_reject_missing_targets_and_ignore_scratch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            repository_root = Path(temp_name)
            (repository_root / "README.md").write_text("root\n", encoding="utf-8")
            docs = repository_root / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text("[missing](missing.md)\n", encoding="utf-8")
            scratch = repository_root / ".superpowers/sdd"
            scratch.mkdir(parents=True)
            (scratch / "scratch.md").write_text(
                "[ignored](missing.md)\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "docs/guide.md -> missing.md is missing"):
                verify_repository_markdown_links(repository_root)

            (docs / "missing.md").write_text("present\n", encoding="utf-8")
            installed_skill = repository_root / ".agents/skills/installed-skill"
            installed_skill.mkdir(parents=True)
            (installed_skill / "generated.md").write_text(
                "[ignored](missing.md)\n",
                encoding="utf-8",
            )
            agent_notes = repository_root / ".agents/notes.md"
            agent_notes.write_text("[included](included.md)\n", encoding="utf-8")
            (repository_root / ".agents/included.md").write_text("present\n", encoding="utf-8")
            self.assertEqual(2, verify_repository_markdown_links(repository_root))

    def test_unsupported_frontmatter_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            skill_root = Path(temp_name) / "example"
            skill_root.mkdir()
            (skill_root / "SKILL.md").write_text(
                "---\nname: example\ndescription: >\n  folded YAML is unsupported\n---\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unsupported YAML"):
                validate_skill_schema(skill_root)


if __name__ == "__main__":
    unittest.main()
