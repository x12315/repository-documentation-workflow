#!/usr/bin/env python3
"""Install the released skill into a temporary Agent Skills consumer and verify its copy."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from verify_skill_schema import validate_skill_schema


SKILL_NAME = "repository-documentation-workflow"
SKILLS_CLI = "skills@1.5.23"
MINIMUM_NODE_VERSION = (22, 20)
CLI_PROBE_TIMEOUT_SECONDS = 10
INSTALL_TIMEOUT_SECONDS = 180
NODE_VERSION_RE = re.compile(r"v(\d+)\.(\d+)\.\d+\s*\Z")


def _check_cli_versions() -> None:
    """Require executable Node and npx, with Node at least 22.20."""
    node = subprocess.run(
        ["node", "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=CLI_PROBE_TIMEOUT_SECONDS,
    )
    match = NODE_VERSION_RE.fullmatch(node.stdout)
    if match is None:
        raise ValueError(f"cannot parse node version: {node.stdout.strip()!r}")
    node_version = (int(match.group(1)), int(match.group(2)))
    if node_version < MINIMUM_NODE_VERSION:
        raise ValueError("node must be at least 22.20")
    subprocess.run(
        ["npx", "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=CLI_PROBE_TIMEOUT_SECONDS,
    )


def _file_inventory(root: Path) -> dict[Path, bytes]:
    """Return regular-file bytes below root and reject symlinks anywhere in its tree."""
    if root.is_symlink():
        raise ValueError(f"skill tree contains symlink: {root}")
    inventory: dict[Path, bytes] = {}
    for current_name, directories, filenames in os.walk(root, followlinks=False):
        current = Path(current_name)
        for name in [*directories, *filenames]:
            path = current / name
            if path.is_symlink():
                raise ValueError(f"skill tree contains symlink: {path}")
            if path.is_file():
                inventory[path.relative_to(root)] = path.read_bytes()
    return inventory


def install_and_verify(
    repository_root: Path,
    runner: Callable[..., subprocess.CompletedProcess[object]] = subprocess.run,
) -> int:
    """Install the skill into a temporary consumer and return its verified file count."""
    resolved_root = repository_root.resolve()
    source_root = resolved_root / "skills" / SKILL_NAME
    source_inventory = _file_inventory(source_root)
    _check_cli_versions()

    with tempfile.TemporaryDirectory() as temporary_name:
        consumer_root = Path(temporary_name)
        command = [
            "npx",
            "--yes",
            SKILLS_CLI,
            "add",
            str(resolved_root),
            "--skill",
            SKILL_NAME,
            "--agent",
            "codex",
            "--copy",
            "--yes",
        ]
        runner(command, check=True, cwd=consumer_root, timeout=INSTALL_TIMEOUT_SECONDS)
        installed_root = consumer_root / ".agents" / "skills" / SKILL_NAME
        installed_inventory = _file_inventory(installed_root)
        try:
            validate_skill_schema(installed_root)
        except (OSError, UnicodeError, ValueError) as error:
            raise ValueError(f"installed skill schema is invalid: {error}") from error
        if source_inventory.keys() != installed_inventory.keys():
            raise ValueError("installed skill file inventory differs from source")
        for relative_path, source_bytes in source_inventory.items():
            if installed_inventory[relative_path] != source_bytes:
                raise ValueError(f"installed skill bytes differ: {relative_path}")
    return len(source_inventory)


def main() -> int:
    """Run the Agent Skills CLI smoke test for this repository."""
    try:
        count = install_and_verify(Path(__file__).resolve().parents[1])
    except subprocess.TimeoutExpired as error:
        print(
            f"Agent Skills CLI installation smoke test timed out after {error.timeout} seconds: {error.cmd}",
            file=sys.stderr,
        )
        return 1
    except (OSError, subprocess.CalledProcessError, UnicodeError, ValueError) as error:
        print(f"Agent Skills CLI installation smoke test failed: {error}", file=sys.stderr)
        return error.returncode if isinstance(error, subprocess.CalledProcessError) else 1
    print(f"installed and verified {SKILL_NAME} ({count} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
