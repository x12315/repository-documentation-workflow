#!/usr/bin/env python3
"""Verify recorded forward model-review runs for the current plugin version."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from verify_distribution import validate_plugin_manifest


REVIEWER_ROLES = {"cold-reader", "coverage-reviewer"}
VERDICTS = {"PASS", "FAIL"}
VERDICT_LINE_RE = re.compile(r"verdict:\s*(PASS|FAIL)\s*$")


def load_json_yaml(path: Path) -> dict:
    """Load one JSON-compatible YAML object from disk."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON-compatible YAML {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def require_nonempty_string(record: dict, field: str, location: str) -> str:
    """Return a required non-blank string field from a record object."""
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location}.{field} must be a non-empty string")
    return value


def require_object(record: dict, field: str, location: str) -> dict:
    """Return a required object field from a record object."""
    value = record.get(field)
    if not isinstance(value, dict):
        raise ValueError(f"{location}.{field} must be an object")
    return value


def resolve_evidence_path(run_root: Path, relative_path: object, field: str) -> Path:
    """Resolve a required evidence file without permitting a run-root escape."""
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise ValueError(f"{field} must be a non-empty relative path")
    path = Path(relative_path)
    if path.is_absolute():
        raise ValueError(f"{field} must be relative to the forward run")
    resolved = (run_root / path).resolve()
    try:
        resolved.relative_to(run_root)
    except ValueError as error:
        raise ValueError(f"{field} leaves the forward run") from error
    if not resolved.is_file():
        raise ValueError(f"{field} does not exist: {relative_path}")
    return resolved


def first_result_verdict(result_path: Path) -> str:
    """Return the first verdict line from a raw reviewer result."""
    try:
        lines = result_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"cannot read reviewer result {result_path}: {error}") from error
    for line in lines:
        if line.startswith("verdict:"):
            match = VERDICT_LINE_RE.fullmatch(line)
            if match is None:
                raise ValueError(f"first verdict in {result_path} must be PASS or FAIL")
            return match.group(1)
    raise ValueError(f"reviewer result has no verdict: {result_path}")


def validate_forward_run(run_root: Path, expected_version: str) -> int:
    """Validate one recorded run and return its number of reviewer results."""
    run_root = run_root.resolve()
    record = load_json_yaml(run_root / "record.yaml")
    if record.get("schema_version") != 1:
        raise ValueError("record.schema_version must be 1")
    if record.get("release_version") != expected_version:
        raise ValueError("record.release_version must match the plugin version")
    require_nonempty_string(record, "case", "record")
    if record.get("model_reviews_run") is not True:
        raise ValueError("record.model_reviews_run must be true")

    author = require_object(record, "author", "record")
    require_nonempty_string(author, "context_id", "record.author")
    require_nonempty_string(author, "model", "record.author")
    resolve_evidence_path(run_root, author.get("report_path"), "record.author.report_path")

    rounds = record.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        raise ValueError("record.rounds must be a non-empty array")

    reviewer_ids: set[str] = set()
    round_roles: dict[int, set[str]] = {}
    round_verdicts: dict[int, list[str]] = {}
    reviewer_count = 0
    for reviewer_index, reviewer in enumerate(rounds, start=1):
        location = f"record.rounds[{reviewer_index}]"
        if not isinstance(reviewer, dict):
            raise ValueError(f"{location} must be an object")
        round_number = reviewer.get("round")
        if isinstance(round_number, bool) or not isinstance(round_number, int) or round_number < 1:
            raise ValueError(f"{location}.round must be a positive integer")
        role = require_nonempty_string(reviewer, "role", location)
        reviewer_id = require_nonempty_string(reviewer, "reviewer_id", location)
        if reviewer_id in reviewer_ids:
            raise ValueError("reviewer_id must be unique throughout one forward run")
        reviewer_ids.add(reviewer_id)
        require_nonempty_string(reviewer, "model", location)
        verdict = reviewer.get("verdict")
        if verdict not in VERDICTS:
            raise ValueError(f"{location}.verdict must be PASS or FAIL")
        result_path = resolve_evidence_path(run_root, reviewer.get("result_path"), f"{location}.result_path")
        if first_result_verdict(result_path) != verdict:
            raise ValueError(f"{location}.verdict does not match the first result verdict")
        round_roles.setdefault(round_number, set()).add(role)
        round_verdicts.setdefault(round_number, []).append(verdict)
        reviewer_count += 1

    round_numbers = set(round_verdicts)
    if round_numbers != set(range(1, max(round_numbers) + 1)):
        raise ValueError("record.rounds must use continuous round numbers starting at 1")
    for round_number in round_numbers:
        if len(round_verdicts[round_number]) != len(REVIEWER_ROLES) or round_roles[round_number] != REVIEWER_ROLES:
            raise ValueError(f"round {round_number} must contain cold-reader and coverage-reviewer")

    outcome = record.get("outcome")
    final_round = max(round_numbers)
    final_verdicts = round_verdicts[final_round]
    if outcome == "passed":
        if set(final_verdicts) != {"PASS"}:
            raise ValueError("a passed forward run must end with a same-round double PASS")
    elif outcome == "blocked":
        if len(round_numbers) != 3 or "FAIL" not in round_verdicts[3]:
            raise ValueError("a blocked forward run must have three rounds and end with a FAIL")
    else:
        raise ValueError("record.outcome must be passed or blocked")
    return reviewer_count


def validate_version_root(version_root: Path, expected_version: str) -> tuple[int, int]:
    """Validate direct run directories below one resolved version evidence root."""
    if version_root.is_symlink():
        raise ValueError(f"forward-run version root must not be a symlink: {version_root.name}")
    if not version_root.is_dir():
        raise ValueError(f"forward-run evidence is missing for version {expected_version}")
    resolved_version_root = version_root.resolve()
    candidates = sorted(path for path in version_root.iterdir() if path.is_dir() or path.is_symlink())
    if not candidates:
        raise ValueError(f"no forward runs recorded for version {expected_version}")

    reviewer_count = 0
    for candidate in candidates:
        if candidate.is_symlink():
            raise ValueError(f"forward run directory must not be a symlink: {candidate.name}")
        run_root = candidate.resolve()
        try:
            run_root.relative_to(resolved_version_root)
        except ValueError as error:
            raise ValueError(f"forward run directory leaves version root: {candidate.name}") from error
        reviewer_count += validate_forward_run(run_root, expected_version)
    return len(candidates), reviewer_count


def main() -> int:
    """Validate all recorded forward runs for the manifest's current version."""
    if len(sys.argv) != 2:
        print("usage: verify_forward_runs.py REPOSITORY_ROOT", file=sys.stderr)
        return 2
    repository_root = Path(sys.argv[1]).resolve()
    try:
        version = validate_plugin_manifest(repository_root)
        version_root = repository_root / "tests" / "forward-runs" / version
        run_count, reviewer_count = validate_version_root(version_root, version)
    except ValueError as error:
        print(f"forward-run verification failed: {error}", file=sys.stderr)
        return 1
    print(f"verified {run_count} forward run(s) and {reviewer_count} reviewer result(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
