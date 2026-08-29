#!/usr/bin/env python3
"""Deterministic verification for plugin distribution contracts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SEMVER_RE = re.compile(
    r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
REQUIRED_INTERFACE = {
    "displayName",
    "shortDescription",
    "longDescription",
    "developerName",
    "category",
    "capabilities",
    "defaultPrompt",
}


def load_object(path: Path) -> dict:
    """Load a JSON object from disk."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON object {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _inside(root: Path, relative: object, field: str) -> Path:
    """Resolve a local path and reject escapes outside the expected root."""
    if not isinstance(relative, str) or not relative.startswith("./"):
        raise ValueError(f"{field} must start with ./")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"{field} leaves its root") from error
    return resolved


def validate_plugin_manifest(repository_root: Path) -> str:
    """Validate the local plugin manifest and return its strict semver version."""
    manifest = load_object(repository_root / ".codex-plugin/plugin.json")
    required = {"name", "version", "description", "author", "license", "skills", "interface"}
    if missing := required - manifest.keys():
        raise ValueError(f"plugin manifest missing: {', '.join(sorted(missing))}")
    if manifest["name"] != repository_root.name:
        raise ValueError("plugin name must match repository directory")
    version = manifest["version"]
    if not isinstance(version, str) or SEMVER_RE.fullmatch(version) is None:
        raise ValueError("plugin version must use strict semver")
    if manifest["license"] != "Apache-2.0":
        raise ValueError("plugin license must match repository LICENSE")
    author = manifest["author"]
    if not isinstance(author, dict) or not isinstance(author.get("name"), str) or not author["name"].strip():
        raise ValueError("plugin author.name is required")
    interface = manifest["interface"]
    if not isinstance(interface, dict) or REQUIRED_INTERFACE - interface.keys():
        raise ValueError("plugin interface is incomplete")
    skill_root = _inside(repository_root, manifest["skills"], "skills")
    expected_skill = skill_root / manifest["name"] / "SKILL.md"
    if not expected_skill.is_file():
        raise ValueError(f"plugin skill entry is missing: {expected_skill}")
    try:
        changelog = (repository_root / "CHANGELOG.md").read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"cannot read changelog: {error}") from error
    if f"## [{version}]" not in changelog:
        raise ValueError("CHANGELOG does not contain plugin version")
    return version


def validate_marketplace(marketplace_root: Path, expected_plugin_name: str) -> Path:
    """Validate marketplace metadata and return the resolved plugin root."""
    catalog = load_object(marketplace_root / ".agents/plugins/marketplace.json")
    entries = catalog.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1:
        raise ValueError("marketplace must contain exactly one smoke-test plugin")
    entry = entries[0]
    if entry.get("name") != expected_plugin_name:
        raise ValueError("marketplace plugin name mismatch")
    source = entry.get("source")
    expected_path = f"./plugins/{expected_plugin_name}"
    if not isinstance(source, dict) or source.get("source") != "local" or source.get("path") != expected_path:
        raise ValueError(f"source.path must be {expected_path}")
    if entry.get("policy") != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}:
        raise ValueError("marketplace policy mismatch")
    plugin_root = _inside(marketplace_root, expected_path, "source.path")
    if not (plugin_root / ".codex-plugin/plugin.json").is_file():
        raise ValueError("marketplace plugin manifest is missing")
    return plugin_root


def main() -> int:
    """Validate plugin distribution metadata for a repository root."""
    if len(sys.argv) != 2:
        print("usage: verify_distribution.py REPOSITORY_ROOT", file=sys.stderr)
        return 2
    try:
        version = validate_plugin_manifest(Path(sys.argv[1]).resolve())
    except ValueError as error:
        print(f"distribution verification failed: {error}", file=sys.stderr)
        return 1
    print(f"verified plugin distribution {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
