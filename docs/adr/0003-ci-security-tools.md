# 3. Security gates: pip-audit, gitleaks, actionlint, zizmor

**Status:** accepted
**Date:** 2026-10-25

## Context

The repository is public and will hold code that handles minors' data. The existing gates
check that code is correct and authorised, not that it is safe: nothing caught a vulnerable
dependency, a committed secret, or a workflow that hands a token to unpinned third-party code.
The first `pip-audit` run found a known vulnerability in a locked dependency (`certifi`).

## Decision

Two gates join `make ci` and CI, each failing on any finding:

- `make sec` - **pip-audit** checks every locked dependency, dev included, against known
  vulnerabilities; **gitleaks** scans the whole git history for secrets.
- `make workflows` - **actionlint** checks workflow syntax and embedded shell; **zizmor**
  checks workflow security: unpinned actions, excess permissions, persisted credentials,
  template injection, impostor commits.

None of them is a project dependency. The Python tools run through `uvx` at versions pinned in
the `Makefile`; gitleaks is a Go binary that CI downloads at a pinned version and verifies by
checksum. Neither the standard library nor Django does any of this.

Workflows pin every action to a commit SHA and default to `contents: read`. Dependabot keeps
the SHAs current.

## Consequences

`make sec` needs network access. Locally, gitleaks runs only if installed
(`brew install gitleaks`); CI always runs it. A newly published vulnerability can fail CI with
no code change. That is the intended behaviour: bump the package, and do not suppress the
finding.
