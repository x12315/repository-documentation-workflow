"""Verify that a Git checkout does not depend on untracked delivery files."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def verify_tracked_delivery(repository_root: Path) -> int | None:
    """Return checked file count, or None when running outside a Git checkout."""
    probe = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return None

    result = subprocess.run(
        ["git", "-C", str(repository_root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    tracked = {Path(value.decode("utf-8")) for value in result.stdout.split(b"\0") if value}
    delivery_roots = (
        repository_root / ".codex-plugin",
        repository_root / "scripts",
        repository_root / "skills" / "repository-documentation-workflow",
        repository_root / "tests",
    )
    expected = {
        path.relative_to(repository_root)
        for root in delivery_roots
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
    }
    expected.update({Path(".gitignore"), Path("LICENSE"), Path("README.md")})

    untracked = sorted(expected - tracked)
    missing = sorted(path for path in tracked if not (repository_root / path).exists())
    if untracked or missing:
        details = []
        if untracked:
            details.append("untracked delivery files: " + ", ".join(map(str, untracked)))
        if missing:
            details.append("tracked files missing from worktree: " + ", ".join(map(str, missing)))
        raise ValueError("; ".join(details))
    return len(expected)


def main() -> int:
    """Run the tracked-delivery check for a repository root."""
    if len(sys.argv) != 2:
        print("usage: verify_tracked.py REPOSITORY_ROOT", file=sys.stderr)
        return 2
    try:
        checked = verify_tracked_delivery(Path(sys.argv[1]).resolve())
    except (OSError, subprocess.CalledProcessError, UnicodeError, ValueError) as error:
        print(f"tracked delivery verification failed: {error}", file=sys.stderr)
        return 1
    if checked is None:
        print("tracked delivery layer: not run outside a Git checkout")
    else:
        print(f"verified {checked} Git-tracked delivery files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
