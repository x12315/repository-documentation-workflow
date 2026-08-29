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
    def _write_minimal_repository(self, workspace: Path) -> Path:
        repository_root = workspace / "repository-documentation-workflow"
        plugin_name = repository_root.name
        (repository_root / ".codex-plugin").mkdir(parents=True)
        (repository_root / "skills" / plugin_name).mkdir(parents=True)
        (repository_root / ".codex-plugin/plugin.json").write_text(
            json.dumps({
                "name": plugin_name,
                "version": "0.1.0",
                "description": "test plugin",
                "author": {"name": "test"},
                "license": "Apache-2.0",
                "skills": "./skills/",
                "interface": {
                    "displayName": "Test",
                    "shortDescription": "Test",
                    "longDescription": "Test",
                    "developerName": "test",
                    "category": "Productivity",
                    "capabilities": ["Write"],
                    "defaultPrompt": "Test",
                },
            }),
            encoding="utf-8",
        )
        (repository_root / "CHANGELOG.md").write_text("## [0.1.0]", encoding="utf-8")
        (repository_root / "LICENSE").write_text("Apache-2.0", encoding="utf-8")
        (repository_root / "skills" / plugin_name / "SKILL.md").write_text("# Test", encoding="utf-8")
        return repository_root

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

    def test_marketplace_smoke_rejects_symlinked_delivery_surface(self) -> None:
        source_paths = (Path(".codex-plugin/plugin.json"), Path("CHANGELOG.md"), Path("LICENSE"))
        with tempfile.TemporaryDirectory() as temp_name:
            workspace = Path(temp_name)
            for source_path in source_paths:
                with self.subTest(source_path=source_path):
                    repository_root = self._write_minimal_repository(workspace / source_path.stem)
                    source = repository_root / source_path
                    outside = workspace / f"outside-{source_path.stem}"
                    outside.write_bytes(source.read_bytes())
                    source.unlink()
                    source.symlink_to(outside)
                    with self.assertRaisesRegex(ValueError, "source delivery"):
                        validate_marketplace_smoke(repository_root)

            repository_root = self._write_minimal_repository(workspace / "parent")
            source_directory = repository_root / ".codex-plugin"
            outside_directory = workspace / "outside-codex-plugin"
            outside_directory.mkdir()
            (outside_directory / "plugin.json").write_bytes((source_directory / "plugin.json").read_bytes())
            (source_directory / "plugin.json").unlink()
            source_directory.rmdir()
            source_directory.symlink_to(outside_directory, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "source delivery"):
                validate_marketplace_smoke(repository_root)

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
