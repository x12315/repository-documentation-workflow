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

from verify_distribution import SEMVER_RE, validate_marketplace, validate_plugin_manifest  # noqa: E402


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
