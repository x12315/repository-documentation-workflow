#!/usr/bin/env python3
"""Regression tests for the Agent Skills CLI installation smoke check."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from smoke_agent_skills_install import install_and_verify  # noqa: E402


SKILL_NAME = "repository-documentation-workflow"


class AgentSkillsInstallTest(unittest.TestCase):
    def test_runner_receives_exact_copy_install_command_and_consumer_is_cleaned(self) -> None:
        consumer_roots: list[Path] = []

        def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[object]:
            consumer_root = kwargs["cwd"]
            self.assertIsInstance(consumer_root, Path)
            consumer_roots.append(consumer_root)
            self.assertEqual(
                [
                    "npx",
                    "--yes",
                    "skills@1.5.23",
                    "add",
                    str(ROOT.resolve()),
                    "--skill",
                    SKILL_NAME,
                    "--agent",
                    "codex",
                    "--copy",
                    "--yes",
                ],
                command,
            )
            self.assertEqual({"check": True, "cwd": consumer_root}, kwargs)
            shutil.copytree(
                ROOT / "skills" / SKILL_NAME,
                consumer_root / ".agents" / "skills" / SKILL_NAME,
            )
            return subprocess.CompletedProcess(command, 0)

        expected_count = sum(
            path.is_file() for path in (ROOT / "skills" / SKILL_NAME).rglob("*")
        )
        self.assertEqual(expected_count, install_and_verify(ROOT, runner))
        self.assertEqual(1, len(consumer_roots))
        self.assertFalse(consumer_roots[0].exists())

    def test_install_rejects_drifted_skill_tree(self) -> None:
        def replace_with_directory_symlink(root: Path) -> None:
            copied_root = root.with_name("copied")
            root.rename(copied_root)
            root.symlink_to(copied_root, target_is_directory=True)

        mutations = {
            "extra file": lambda root: (root / "extra.txt").write_text("unexpected", encoding="utf-8"),
            "missing file": lambda root: (root / "SKILL.md").unlink(),
            "changed bytes": lambda root: (root / "SKILL.md").write_text("changed", encoding="utf-8"),
            "file symlink": lambda root: (root / "alias").symlink_to(root / "SKILL.md"),
            "directory symlink": lambda root: (root / "aliases").symlink_to(
                root / "references", target_is_directory=True
            ),
            "installed root symlink": replace_with_directory_symlink,
        }

        for description, mutate in mutations.items():
            with self.subTest(description=description):
                def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[object]:
                    consumer_root = kwargs["cwd"]
                    self.assertIsInstance(consumer_root, Path)
                    installed_root = consumer_root / ".agents" / "skills" / SKILL_NAME
                    shutil.copytree(ROOT / "skills" / SKILL_NAME, installed_root)
                    mutate(installed_root)
                    return subprocess.CompletedProcess(command, 0)

                with self.assertRaises(ValueError):
                    install_and_verify(ROOT, runner)


if __name__ == "__main__":
    unittest.main()
