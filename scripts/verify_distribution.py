#!/usr/bin/env python3
"""Deterministic verification for plugin distribution contracts."""

from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path


SEMVER_RE = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?"
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


def _skill_files(skill_root: Path, label: str) -> dict[Path, Path]:
    """Return regular Skill files, rejecting symlinks in the tree."""
    if skill_root.is_symlink() or not skill_root.is_dir():
        raise ValueError(f"{label} skill tree must be a directory without symlinks")
    files = {}
    for path in skill_root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"{label} skill tree must not contain symlinks: {path}")
        if path.is_file():
            files[path.relative_to(skill_root)] = path
    return files


def validate_skill_inventory(source_skill_root: Path, marketplace_skill_root: Path) -> int:
    """Verify copied Skill files exactly match the source Skill inventory and bytes."""
    source_files = _skill_files(source_skill_root, "source")
    marketplace_files = _skill_files(marketplace_skill_root, "marketplace")
    if source_files.keys() != marketplace_files.keys():
        raise ValueError("marketplace skill inventory does not match source")
    for relative_path, source_path in source_files.items():
        if source_path.read_bytes() != marketplace_files[relative_path].read_bytes():
            raise ValueError(f"marketplace skill bytes differ: {relative_path}")
    return len(source_files)


def _source_delivery_file(repository_root: Path, relative_path: Path) -> Path:
    """Return a regular source delivery file without resolving through symlinks."""
    resolved_root = repository_root.resolve()
    source_path = repository_root / relative_path
    try:
        source_path.resolve(strict=True).relative_to(resolved_root)
    except (OSError, ValueError) as error:
        raise ValueError(f"source delivery path leaves repository: {relative_path}") from error
    current = source_path
    while current != repository_root:
        if current.is_symlink():
            raise ValueError(f"source delivery path uses symlink: {relative_path}")
        current = current.parent
    if not source_path.is_file():
        raise ValueError(f"source delivery path must be a regular file: {relative_path}")
    return source_path


def _source_skill_root(repository_root: Path, plugin_name: str) -> Path:
    """Return the source Skill root after rejecting symlinked or escaped paths."""
    resolved_root = repository_root.resolve()
    skill_root = repository_root / "skills" / plugin_name
    try:
        skill_root.resolve(strict=True).relative_to(resolved_root)
    except (OSError, ValueError) as error:
        raise ValueError("source Skill root leaves repository") from error
    current = skill_root
    while current != repository_root:
        if current.is_symlink():
            raise ValueError("source Skill root uses symlink")
        current = current.parent
    if not skill_root.is_dir():
        raise ValueError("source Skill root must be a directory")
    return skill_root


def validate_marketplace_smoke(repository_root: Path) -> int:
    """Build and validate a temporary local marketplace for this plugin."""
    plugin_name = repository_root.name
    source_skill_root = _source_skill_root(repository_root, plugin_name)
    with tempfile.TemporaryDirectory() as temp_name:
        marketplace_root = Path(temp_name)
        plugin_root = marketplace_root / "plugins" / plugin_name
        plugin_root.mkdir(parents=True)
        (marketplace_root / ".agents/plugins").mkdir(parents=True)
        (marketplace_root / ".agents/plugins/marketplace.json").write_text(
            json.dumps({
                "name": "local-smoke-test",
                "plugins": [{
                    "name": plugin_name,
                    "source": {"source": "local", "path": f"./plugins/{plugin_name}"},
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                    "category": "Productivity",
                }],
            }),
            encoding="utf-8",
        )
        source_files = tuple(
            (relative_path, _source_delivery_file(repository_root, relative_path))
            for relative_path in (Path(".codex-plugin/plugin.json"), Path("CHANGELOG.md"), Path("LICENSE"))
        )
        for relative_path, source_path in source_files:
            destination = plugin_root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, destination)
        marketplace_skill_root = plugin_root / "skills" / plugin_name
        shutil.copytree(source_skill_root, marketplace_skill_root, symlinks=True)
        resolved_plugin_root = validate_marketplace(marketplace_root, plugin_name)
        validate_plugin_manifest(resolved_plugin_root)
        return validate_skill_inventory(source_skill_root, marketplace_skill_root)


def main() -> int:
    """Validate plugin distribution metadata for a repository root."""
    if len(sys.argv) != 2:
        print("usage: verify_distribution.py REPOSITORY_ROOT", file=sys.stderr)
        return 2
    try:
        repository_root = Path(sys.argv[1]).resolve()
        version = validate_plugin_manifest(repository_root)
        skill_files = validate_marketplace_smoke(repository_root)
    except (OSError, ValueError) as error:
        print(f"distribution verification failed: {error}", file=sys.stderr)
        return 1
    print(f"verified plugin distribution {version} ({skill_files} skill files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
