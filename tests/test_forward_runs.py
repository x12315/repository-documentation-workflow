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

from verify_forward_runs import validate_forward_run  # noqa: E402


class ForwardRunValidationTest(unittest.TestCase):
    def write_run(self, root: Path) -> Path:
        """Create one valid run record and its referenced evidence."""
        run_root = root / "newcomer-architecture"
        results = run_root / "results"
        results.mkdir(parents=True)
        (run_root / "author-report.md").write_text("author self-check\n", encoding="utf-8")
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
            "rounds": [{
                "round": 1,
                "reviewers": [
                    {
                        "role": "cold-reader",
                        "reviewer_id": "/root/forward_cold_reader_r1",
                        "model": "gpt-5 (exact runtime revision not exposed)",
                        "verdict": "PASS",
                        "result_path": "results/round-1-cold-reader.md",
                    },
                    {
                        "role": "coverage-reviewer",
                        "reviewer_id": "/root/forward_coverage_r1",
                        "model": "gpt-5 (exact runtime revision not exposed)",
                        "verdict": "PASS",
                        "result_path": "results/round-1-coverage-reviewer.md",
                    },
                ],
            }],
        }
        (run_root / "record.yaml").write_text(json.dumps(record), encoding="utf-8")
        return run_root

    def load_record(self, run_root: Path) -> dict:
        """Load the JSON-compatible YAML record under test."""
        return json.loads((run_root / "record.yaml").read_text(encoding="utf-8"))

    def write_record(self, run_root: Path, record: dict) -> None:
        """Persist a modified JSON-compatible YAML record."""
        (run_root / "record.yaml").write_text(json.dumps(record), encoding="utf-8")

    def test_rejects_duplicate_reviewer_id_within_a_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_root = self.write_run(Path(temporary_directory))
            record = self.load_record(run_root)
            reviewers = record["rounds"][0]["reviewers"]
            reviewers[1]["reviewer_id"] = reviewers[0]["reviewer_id"]
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


if __name__ == "__main__":
    unittest.main()
