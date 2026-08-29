#!/usr/bin/env python3
"""Negative regression tests for deterministic verification boundaries."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from upstream_lock import validate_lock  # noqa: E402
from verify_release import verify_local_markdown_links  # noqa: E402
from verify_skill_schema import validate_skill_schema  # noqa: E402


class VerificationBoundaryTest(unittest.TestCase):
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
