#!/usr/bin/env python3
"""Regression tests for plugin distribution contracts."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_distribution import (  # noqa: E402
    SEMVER_RE,
    validate_marketplace,
    validate_marketplace_smoke,
    validate_plugin_manifest,
    validate_skill_inventory,
)


class DistributionTest(unittest.TestCase):
    def test_semver_requires_nonempty_identifiers_and_canonical_numeric_prereleases(self) -> None:
        for version in ("1.0.0", "1.0.0-alpha.1+build.5"):
            with self.subTest(version=version):
                self.assertIsNotNone(SEMVER_RE.fullmatch(version))

        for version in ("1.0.0-01", "1.0.0-.", "1.0.0-alpha..1", "1١.0.0", "1.0.0-١a"):
            with self.subTest(version=version):
                self.assertIsNone(SEMVER_RE.fullmatch(version))

    def test_repository_manifest_is_valid_and_versioned(self) -> None:
        self.assertEqual("0.1.0", validate_plugin_manifest(ROOT))

    def test_marketplace_smoke_validates_the_copied_plugin_inventory(self) -> None:
        source_files = [path for path in (ROOT / "skills/repository-documentation-workflow").rglob("*") if path.is_file()]
        self.assertEqual(len(source_files), validate_marketplace_smoke(ROOT))

    def test_skill_inventory_rejects_bytes_and_symlink_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            source = root / "source"
            copied = root / "copied"
            for skill_root in (source, copied):
                skill_root.mkdir()
                (skill_root / "SKILL.md").write_text("same", encoding="utf-8")

            self.assertEqual(1, validate_skill_inventory(source, copied))
            (copied / "extra.md").write_text("extra", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "skill inventory"):
                validate_skill_inventory(source, copied)

            (copied / "extra.md").unlink()
            (copied / "SKILL.md").write_text("drifted", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "skill bytes"):
                validate_skill_inventory(source, copied)

            (copied / "SKILL.md").write_text("same", encoding="utf-8")
            (source / "linked.md").symlink_to(source / "SKILL.md")
            with self.assertRaisesRegex(ValueError, "source skill tree.*symlink"):
                validate_skill_inventory(source, copied)

            (source / "linked.md").unlink()
            (copied / "linked.md").symlink_to(copied / "SKILL.md")
            with self.assertRaisesRegex(ValueError, "marketplace skill tree.*symlink"):
                validate_skill_inventory(source, copied)

    def test_marketplace_rejects_invalid_plugin_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            (root / ".agents/plugins").mkdir(parents=True)

            marketplace = root / ".agents/plugins/marketplace.json"
            marketplace.write_text(
                json.dumps({
                    "name": "local-test",
                    "plugins": [{
                        "name": "repository-documentation-workflow",
                        "source": {"source": "local", "path": "../escape"},
                        "policy": {
                            "installation": "AVAILABLE",
                            "authentication": "ON_INSTALL",
                        },
                        "category": "Productivity",
                    }],
                }),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "source.path"):
                validate_marketplace(root, "repository-documentation-workflow")

            marketplace.write_text(
                json.dumps({
                    "name": "local-test",
                    "plugins": [{
                        "name": "repository-documentation-workflow-drifted",
                        "source": {
                            "source": "local",
                            "path": "./plugins/repository-documentation-workflow",
                        },
                        "policy": {
                            "installation": "AVAILABLE",
                            "authentication": "ON_INSTALL",
                        },
                        "category": "Productivity",
                    }],
                }),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "name"):
                validate_marketplace(root, "repository-documentation-workflow")


if __name__ == "__main__":
    unittest.main()
