#!/usr/bin/env python3
"""Regression tests for sync preflight and batch rollback."""

from __future__ import annotations

import copy
import importlib.machinery
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load_script(name: str):
    path = ROOT / "scripts" / name
    loader = importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class SyncUpstreamsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.skill_root = Path(self.temp.name) / "skill"
        (self.skill_root / "references/upstream/source-a").mkdir(parents=True)
        (self.skill_root / "licenses").mkdir()
        self.targets = [
            self.skill_root / "references/upstream/source-a/SOURCE.md",
            self.skill_root / "licenses/source-a-MIT.txt",
        ]
        self.original = {self.targets[0]: b"old source", self.targets[1]: b"old license"}
        for path, content in self.original.items():
            path.write_bytes(content)
        self.new = {"SKILL.md": b"new source", "LICENSE": b"new license"}
        self.lock = {
            "version": 1,
            "updated_at": "2026-08-29",
            "sources": [{
                "id": "source-a",
                "repository": "https://github.com/example/source-a",
                "commit": "a" * 40,
                "license": "MIT",
                "files": [
                    {"upstream_path": name, "vendored_path": str(target.relative_to(self.skill_root)), "sha256": __import__("hashlib").sha256(self.new[name]).hexdigest()}
                    for name, target in zip(self.new, self.targets)
                ],
            }],
        }

    def assert_original_bytes(self) -> None:
        self.assertEqual(self.original, {path: path.read_bytes() for path in self.targets})

    def test_second_replace_failure_rolls_back_every_target(self) -> None:
        module = load_script("sync-upstreams")
        replacements = 0

        def fail_second(source: Path, destination: Path) -> None:
            nonlocal replacements
            replacements += 1
            if replacements == 2:
                raise OSError("injected second replace failure")
            module.os.replace(source, destination)

        with self.assertRaises(module.SyncError):
            module.sync_upstreams(
                self.lock,
                self.skill_root,
                lambda _source, item: self.new[item.upstream_path.as_posix()],
                replace_file=fail_second,
            )
        self.assert_original_bytes()

    def test_post_verify_failure_rolls_back_every_target(self) -> None:
        module = load_script("sync-upstreams")

        def fail_verify() -> None:
            raise ValueError("injected post verification failure")

        with self.assertRaises(module.SyncError):
            module.sync_upstreams(
                self.lock,
                self.skill_root,
                lambda _source, item: self.new[item.upstream_path.as_posix()],
                post_verify=fail_verify,
            )
        self.assert_original_bytes()

    def test_invalid_schema_and_duplicate_target_fail_before_fetch(self) -> None:
        module = load_script("sync-upstreams")
        fetched = False

        def fetch(_source, _item):
            nonlocal fetched
            fetched = True
            return b"unused"

        for mutation in ("license", "duplicate"):
            with self.subTest(mutation=mutation):
                lock = copy.deepcopy(self.lock)
                if mutation == "license":
                    lock["sources"][0]["license"] = {"name": "MIT"}
                else:
                    lock["sources"][0]["files"][1]["vendored_path"] = lock["sources"][0]["files"][0]["vendored_path"]
                with self.assertRaises((module.SyncError, ValueError)):
                    module.sync_upstreams(lock, self.skill_root, fetch)
                self.assertFalse(fetched)
                self.assert_original_bytes()


if __name__ == "__main__":
    unittest.main()
