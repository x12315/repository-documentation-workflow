"""Verify that a Git checkout does not depend on untracked delivery files."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _check_ignore_rule(
    repository_root: Path,
    relative_path: Path,
    *,
    excludes_file: str | None = None,
) -> tuple[Path, int, str, Path] | None:
    """Return the Git ignore rule that matches a relative path, if any."""
    command = [
        "git",
        *(["-c", f"core.excludesFile={excludes_file}"] if excludes_file else []),
        "-C",
        str(repository_root),
        "check-ignore",
        "--no-index",
        "--verbose",
        "-z",
        "--stdin",
    ]
    result = subprocess.run(
        command,
        input=relative_path.as_posix().encode("utf-8") + b"\0",
        capture_output=True,
    )
    if result.returncode == 1:
        return None
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            command,
            output=result.stdout,
            stderr=result.stderr,
        )

    source, line_number, pattern, pathname, terminator = result.stdout.split(b"\0")
    if terminator:
        raise ValueError("Git ignore output is missing its NUL terminator")
    return (
        Path(source.decode("utf-8")),
        int(line_number),
        pattern.decode("utf-8"),
        Path(pathname.decode("utf-8")),
    )


def _is_ignored_by_repository(repository_root: Path, relative_path: Path) -> bool:
    """Return whether a worktree `.gitignore` ignores a relative path."""
    matching_rule = _check_ignore_rule(repository_root, relative_path)
    if matching_rule is None:
        return False

    source, line_number, pattern, pathname = matching_rule
    if pattern.startswith("!"):
        return False

    worktree_root = repository_root.resolve()
    source_path = (worktree_root / source).resolve()
    target_path = Path(os.path.normpath(worktree_root / relative_path))
    git_directory = worktree_root / ".git"
    if not (
        source_path.name == ".gitignore"
        and source_path.is_relative_to(worktree_root)
        and not source_path.is_relative_to(git_directory)
        and target_path.is_relative_to(source_path.parent)
    ):
        return False

    repository_rule = _check_ignore_rule(
        repository_root,
        relative_path,
        excludes_file=os.devnull,
    )
    if repository_rule is None:
        return False

    repository_source, repository_line, repository_pattern, repository_path = repository_rule
    return (
        (worktree_root / repository_source).resolve() == source_path
        and repository_line == line_number
        and repository_pattern == pattern
        and repository_path == pathname
    )


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
        repository_root / ".github",
        repository_root / ".codex-plugin",
        repository_root / "docs",
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
    expected.update({
        Path(".gitignore"),
        Path("LICENSE"),
        Path("README.md"),
        Path("CHANGELOG.md"),
        Path("CODE_OF_CONDUCT.md"),
        Path("CONTRIBUTING.md"),
        Path("SECURITY.md"),
    })
    expected = {
        path
        for path in expected
        if not _is_ignored_by_repository(repository_root, path)
    }

    ignored_tracked = sorted(
        path for path in tracked if _is_ignored_by_repository(repository_root, path)
    )
    if ignored_tracked:
        raise ValueError(
            "tracked files match repository ignore rules: "
            + ", ".join(map(str, ignored_tracked))
        )
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
