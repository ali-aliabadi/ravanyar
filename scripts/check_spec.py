#!/usr/bin/env python3
"""Reject implementation PRs that no approved, already-merged spec authorises.

Passes when the PR touches no application code. Otherwise it needs a SPEC-NNNN id in the
branch name or PR title, and that spec must already be merged and approved on the base
branch. A PR cannot introduce its own authorisation: the spec lands first, in its own PR.
"""

import os
import re
import subprocess
import sys

from check_spec_format import front_matter

SPEC_ID = re.compile(r"SPEC-\d{4}")
GUARDED = ("src/",)


def is_approved(spec_md: str) -> bool:
    """Read status the way the format gate does, so the template's trailing comment is allowed."""
    return front_matter(spec_md).get("status") == "approved"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def main() -> int:
    base = os.environ.get("BASE_REF", "origin/main")
    head = os.environ.get("HEAD_REF", "HEAD")

    changed = git("diff", "--name-only", f"{base}...{head}").splitlines()
    guarded = [f for f in changed if f.startswith(GUARDED)]
    if not guarded:
        print("no application code changed - spec gate waived")
        return 0

    branch = os.environ.get("BRANCH_NAME") or git("rev-parse", "--abbrev-ref", "HEAD")
    context = f"{os.environ.get('PR_TITLE', '')} {branch}"
    found = SPEC_ID.search(context)
    if not found:
        print(f"This PR changes {len(guarded)} file(s) under src/ but names no spec.")
        print("Put a SPEC-NNNN id in the branch name or PR title,")
        print("for example: feat/SPEC-0001-tutor-replies")
        return 1
    spec_id = found.group()

    spec_dirs = git("ls-tree", "-d", "--name-only", base, "specs/").splitlines()
    dirs = [d for d in spec_dirs if spec_id in d]
    if not dirs:
        print(f"{spec_id} is not merged on {base}. Merge the spec PR before the implementation PR.")
        return 1

    body = git("show", f"{base}:{dirs[0]}/spec.md")
    if not is_approved(body):
        print(f"{spec_id} exists on {base} but is not `status: approved`.")
        return 1

    print(f"{spec_id} is merged and approved - {len(guarded)} guarded file(s) authorised")
    return 0


if __name__ == "__main__":
    sys.exit(main())
