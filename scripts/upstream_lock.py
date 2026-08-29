"""Parse and verify the JSON-compatible YAML upstream lock."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath


COMMIT_RE = re.compile(r"[0-9a-f]{40}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
SOURCE_ID_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?")
REPOSITORY_RE = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")


@dataclass(frozen=True)
class LockedFile:
    upstream_path: PurePosixPath
    vendored_path: PurePosixPath
    sha256: str


@dataclass(frozen=True)
class LockedSource:
    source_id: str
    owner: str
    repository_name: str
    commit: str
    license_name: str
    files: tuple[LockedFile, ...]


def load_lock(lock_path: Path) -> object:
    """Read a lock file whose `.yaml` syntax is deliberately limited to JSON."""
    try:
        return json.loads(lock_path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"cannot read {lock_path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"cannot parse {lock_path}: only JSON-compatible YAML is accepted: {error}"
        ) from error


def _require_exact_fields(value: dict, required: set[str], location: str) -> None:
    missing = required - value.keys()
    extra = value.keys() - required
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing {', '.join(sorted(missing))}")
        if extra:
            details.append(f"unknown {', '.join(sorted(extra))}")
        raise ValueError(f"{location}: {'; '.join(details)}")


def _relative_path(value: object, field: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"{field} must stay inside the skill directory: {value}")
    return path


def validate_lock(lock: object, skill_root: Path, *, check_inventory: bool = True) -> tuple[LockedSource, ...]:
    """Validate the complete lock schema and optionally its vendored-file inventory."""
    if not isinstance(lock, dict):
        raise ValueError("lock root must be an object")
    _require_exact_fields(lock, {"version", "updated_at", "sources"}, "lock")
    if lock["version"] != 1:
        raise ValueError("version must be 1")
    if not isinstance(lock["updated_at"], str):
        raise ValueError("updated_at must be an ISO date string")
    try:
        if date.fromisoformat(lock["updated_at"]).isoformat() != lock["updated_at"]:
            raise ValueError
    except ValueError as error:
        raise ValueError("updated_at must use YYYY-MM-DD") from error
    if not isinstance(lock["sources"], list) or not lock["sources"]:
        raise ValueError("sources must be a non-empty list")

    source_ids: set[str] = set()
    vendored_paths: set[PurePosixPath] = set()
    sources: list[LockedSource] = []
    for source_index, source in enumerate(lock["sources"]):
        location = f"sources[{source_index}]"
        if not isinstance(source, dict):
            raise ValueError(f"{location} must be an object")
        _require_exact_fields(source, {"id", "repository", "commit", "license", "files"}, location)
        source_id = source["id"]
        if not isinstance(source_id, str) or SOURCE_ID_RE.fullmatch(source_id) is None:
            raise ValueError(f"{location}.id must use lowercase kebab-case")
        if source_id in source_ids:
            raise ValueError(f"duplicate source id: {source_id}")
        source_ids.add(source_id)

        repository = source["repository"]
        repository_match = REPOSITORY_RE.fullmatch(repository) if isinstance(repository, str) else None
        if repository_match is None:
            raise ValueError(f"{source_id}.repository must be a GitHub HTTPS repository")
        commit = source["commit"]
        if not isinstance(commit, str) or COMMIT_RE.fullmatch(commit) is None:
            raise ValueError(f"{source_id}.commit must be a full lowercase SHA")
        license_name = source["license"]
        if not isinstance(license_name, str) or not license_name.strip():
            raise ValueError(f"{source_id}.license must be a non-empty string")
        if not isinstance(source["files"], list) or not source["files"]:
            raise ValueError(f"{source_id}.files must be a non-empty list")

        files: list[LockedFile] = []
        upstream_paths: set[PurePosixPath] = set()
        for file_index, item in enumerate(source["files"]):
            item_location = f"{source_id}.files[{file_index}]"
            if not isinstance(item, dict):
                raise ValueError(f"{item_location} must be an object")
            _require_exact_fields(item, {"upstream_path", "vendored_path", "sha256"}, item_location)
            upstream_path = _relative_path(item["upstream_path"], f"{item_location}.upstream_path")
            vendored_path = _relative_path(item["vendored_path"], f"{item_location}.vendored_path")
            if vendored_path.parts[0] == "references":
                if len(vendored_path.parts) < 3 or vendored_path.parts[1] != "upstream":
                    raise ValueError(f"vendored reference must live in references/upstream/: {vendored_path}")
            elif vendored_path.parts[0] != "licenses":
                raise ValueError(f"vendored file must live in references/upstream/ or licenses/: {vendored_path}")
            if upstream_path in upstream_paths:
                raise ValueError(f"{source_id}: duplicate upstream path: {upstream_path}")
            if vendored_path in vendored_paths:
                raise ValueError(f"duplicate vendored path: {vendored_path}")
            upstream_paths.add(upstream_path)
            vendored_paths.add(vendored_path)
            digest = item["sha256"]
            if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
                raise ValueError(f"{item_location}.sha256 must be 64 lowercase hex characters")
            files.append(LockedFile(upstream_path, vendored_path, digest))

        owner, repository_name = repository_match.groups()
        sources.append(LockedSource(source_id, owner, repository_name, commit, license_name, tuple(files)))

    if check_inventory:
        actual_paths = {
            path.relative_to(skill_root).as_posix()
            for root in (skill_root / "references" / "upstream", skill_root / "licenses")
            if root.exists()
            for path in root.rglob("*")
            if path.is_file()
        }
        expected_paths = {path.as_posix() for path in vendored_paths}
        unlocked = sorted(actual_paths - expected_paths)
        missing = sorted(expected_paths - actual_paths)
        if unlocked:
            raise ValueError(f"unlocked vendored files: {', '.join(unlocked)}")
        if missing:
            raise ValueError(f"missing vendored files: {', '.join(missing)}")

    return tuple(sources)


def verify_snapshot(lock: object, skill_root: Path) -> tuple[int, int]:
    """Verify schema, inventory, and bytes for every locked snapshot."""
    sources = validate_lock(lock, skill_root)
    verified = 0
    for source in sources:
        for item in source.files:
            path = skill_root.joinpath(*item.vendored_path.parts)
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != item.sha256:
                raise ValueError(
                    f"hash mismatch for {item.vendored_path}: expected {item.sha256}, got {actual}"
                )
            verified += 1
    return verified, len(sources)
