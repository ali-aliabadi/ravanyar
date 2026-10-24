#!/usr/bin/env python3
"""Reject files too long for an agent to hold in its head. Run by `make lint` and CI."""

import subprocess
import sys
from pathlib import Path

DEFAULT_MAX = 300
TEST_MAX = 500


def limit_for(path: Path) -> int | None:
    """None means exempt: migrations are generated, their length says nothing."""
    parts = path.parts
    if "migrations" in parts:
        return None
    if "tests" in parts or path.name.startswith("test_"):
        return TEST_MAX
    return DEFAULT_MAX


def main() -> int:
    # --others: a new file fails here before its first `git add`, not only once it is committed.
    files = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.py"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    violations = []
    for name in files:
        path = Path(name)
        cap = limit_for(path)
        if cap is None or not path.exists():
            continue
        lines = len(path.read_text(encoding="utf-8").splitlines())
        if lines > cap:
            violations.append(f"{name}: {lines} lines (max {cap})")
    if violations:
        print("Files over the line limit. Split them into smaller modules:\n")
        print("\n".join(f"- {v}" for v in violations))
        return 1
    print(f"file length ok ({len(files)} files, max {DEFAULT_MAX}/{TEST_MAX} for tests)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
