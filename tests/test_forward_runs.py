#!/usr/bin/env python3
"""Regression tests for recorded forward model reviews."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_forward_runs import validate_forward_run, validate_version_root  # noqa: E402


class ForwardRunValidationTest(unittest.TestCase):
    def write_run(self, root: Path) -> Path:
        """Create one valid run record and its referenced evidence."""
        run_root = root / "newcomer-architecture"
        results = run_root / "results"
        author_input = run_root / "author-input"
        results.mkdir(parents=True)
        author_input.mkdir()
        (run_root / "author-report.md").write_text("author self-check\n", encoding="utf-8")
        (author_input / "request.md").write_text("author request\n", encoding="utf-8")
        (author_input / "source-packet.md").write_text("author source packet\n", encoding="utf-8")
        (run_root / "author-contract.yaml").write_text(
            json.dumps({
                "primary_reader": "newcomer",
                "entry_state": "needs an overview",
                "exit_outcomes": ["understands the architecture"],
                "reading_mode": "hybrid",
                "scope": "architecture overview",
                "mainline": "follow one request",
            }),
            encoding="utf-8",
        )
        (run_root / "fact-ledger.md").write_text("fact ledger\n", encoding="utf-8")
        (run_root / "draft.md").write_text("draft\n", encoding="utf-8")
        (run_root / "skill-change-summary.md").write_text("summary\n", encoding="utf-8")
        (results / "round-1-cold-reader.md").write_text("verdict: PASS\n", encoding="utf-8")
        (results / "round-1-coverage-reviewer.md").write_text("verdict: PASS\n", encoding="utf-8")
        record = {
            "schema_version": 1,
            "release_version": "0.1.0",
            "case": "newcomer-architecture",
            "model_reviews_run": True,
            "outcome": "passed",
            "author": {
                "context_id": "/root/forward_author_round1",
                "model": "gpt-5 (exact runtime revision not exposed)",
                "report_path": "author-report.md",
            },
            "rounds": [
                {
                    "round": 1,
                    "role": "cold-reader",
                    "reviewer_id": "/root/forward_cold_reader_r1",
                    "model": "gpt-5 (exact runtime revision not exposed)",
                    "verdict": "PASS",
                    "result_path": "results/round-1-cold-reader.md",
                },
                {
                    "round": 1,
                    "role": "coverage-reviewer",
                    "reviewer_id": "/root/forward_coverage_r1",
                    "model": "gpt-5 (exact runtime revision not exposed)",
                    "verdict": "PASS",
                    "result_path": "results/round-1-coverage-reviewer.md",
                },
            ],
        }
        (run_root / "record.yaml").write_text(json.dumps(record), encoding="utf-8")
        return run_root

    def load_record(self, run_root: Path) -> dict:
        """Load the JSON-compatible YAML record under test."""
        return json.loads((run_root / "record.yaml").read_text(encoding="utf-8"))

    def write_record(self, run_root: Path, record: dict) -> None:
        """Persist a modified JSON-compatible YAML record."""
        (run_root / "record.yaml").write_text(json.dumps(record), encoding="utf-8")

    def load_author_contract(self, run_root: Path) -> dict:
        """Load the JSON-compatible author contract under test."""
        return json.loads((run_root / "author-contract.yaml").read_text(encoding="utf-8"))

    def write_author_contract(self, run_root: Path, contract: dict) -> None:
        """Persist a modified JSON-compatible author contract."""
        (run_root / "author-contract.yaml").write_text(json.dumps(contract), encoding="utf-8")

    def test_rejects_duplicate_reviewer_id_within_a_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_root = self.write_run(Path(temporary_directory))
            record = self.load_record(run_root)
            record["rounds"][1]["reviewer_id"] = record["rounds"][0]["reviewer_id"]
            self.write_record(run_root, record)

            with self.assertRaisesRegex(ValueError, "reviewer_id.*unique"):
                validate_forward_run(run_root, "0.1.0")

    def test_rejects_result_verdict_that_differs_from_the_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_root = self.write_run(Path(temporary_directory))
            result = run_root / "results/round-1-cold-reader.md"
            result.write_text("verdict: FAIL\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "verdict"):
                validate_forward_run(run_root, "0.1.0")

    def test_accepts_a_same_round_double_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_root = self.write_run(Path(temporary_directory))

            self.assertEqual(2, validate_forward_run(run_root, "0.1.0"))

    def test_rejects_an_empty_author_contract_object(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_root = self.write_run(Path(temporary_directory))
            self.write_author_contract(run_root, {})

            with self.assertRaisesRegex(ValueError, "primary_reader is required"):
                validate_forward_run(run_root, "0.1.0")

    def test_rejects_missing_or_empty_author_contract_fields(self) -> None:
        for field, value in (("scope", None), ("mainline", "")):
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as temporary_directory:
                run_root = self.write_run(Path(temporary_directory))
                contract = self.load_author_contract(run_root)
                if value is None:
                    del contract[field]
                else:
                    contract[field] = value
                self.write_author_contract(run_root, contract)

                with self.assertRaisesRegex(ValueError, f"{field} is required"):
                    validate_forward_run(run_root, "0.1.0")

    def test_rejects_an_invalid_author_contract_reading_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_root = self.write_run(Path(temporary_directory))
            contract = self.load_author_contract(run_root)
            contract["reading_mode"] = "random"
            self.write_author_contract(run_root, contract)

            with self.assertRaisesRegex(ValueError, "invalid reading_mode"):
                validate_forward_run(run_root, "0.1.0")

    def test_rejects_a_missing_required_evidence_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_root = self.write_run(Path(temporary_directory))
            (run_root / "fact-ledger.md").unlink()

            with self.assertRaisesRegex(ValueError, "required evidence"):
                validate_forward_run(run_root, "0.1.0")

    def test_rejects_an_empty_required_evidence_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_root = self.write_run(Path(temporary_directory))
            (run_root / "draft.md").write_text("", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "non-empty"):
                validate_forward_run(run_root, "0.1.0")

    def test_rejects_a_symlinked_required_evidence_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_root = self.write_run(Path(temporary_directory))
            draft = run_root / "draft.md"
            target = run_root / "draft-target.md"
            draft.rename(target)
            draft.symlink_to(target)

            with self.assertRaisesRegex(ValueError, "symlink"):
                validate_forward_run(run_root, "0.1.0")

    def test_rejects_a_symlinked_required_evidence_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_root = self.write_run(Path(temporary_directory))
            author_input = run_root / "author-input"
            target = run_root / "author-input-target"
            author_input.rename(target)
            author_input.symlink_to(target, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "symlink"):
                validate_forward_run(run_root, "0.1.0")

    def test_rejects_a_symlinked_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_root = self.write_run(Path(temporary_directory))
            record = run_root / "record.yaml"
            target = run_root / "record-target.yaml"
            record.rename(target)
            record.symlink_to(target)

            with self.assertRaisesRegex(ValueError, "symlink"):
                validate_forward_run(run_root, "0.1.0")

    def test_rejects_round_numbers_that_are_not_continuous_from_one(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_root = self.write_run(Path(temporary_directory))
            record = self.load_record(run_root)
            for reviewer in record["rounds"]:
                reviewer["round"] = 2
            self.write_record(run_root, record)

            with self.assertRaisesRegex(ValueError, "continuous"):
                validate_forward_run(run_root, "0.1.0")

    def test_rejects_a_symlinked_run_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            version_root = root / "tests/forward-runs/0.1.0"
            version_root.mkdir(parents=True)
            outside_run = self.write_run(root / "outside")
            (version_root / "escaped-run").symlink_to(outside_run, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "symlink"):
                validate_version_root(version_root, "0.1.0", root)

    def test_rejects_a_symlinked_version_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            outside_version_root = root / "outside/0.1.0"
            outside_version_root.mkdir(parents=True)
            version_root = root / "tests/forward-runs/0.1.0"
            version_root.parent.mkdir(parents=True)
            version_root.symlink_to(outside_version_root, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "symlink"):
                validate_version_root(version_root, "0.1.0", root)

    def test_rejects_a_version_root_reached_through_a_symlinked_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            repository_root = root / "repository"
            repository_root.mkdir()
            outside_tests = root / "outside-tests"
            version_root = outside_tests / "forward-runs/0.1.0"
            version_root.mkdir(parents=True)
            self.write_run(version_root)
            (repository_root / "tests").symlink_to(outside_tests, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "leaves repository"):
                validate_version_root(repository_root / "tests/forward-runs/0.1.0", "0.1.0", repository_root)


if __name__ == "__main__":
    unittest.main()
