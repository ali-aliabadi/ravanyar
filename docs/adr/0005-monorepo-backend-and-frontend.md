# 5. Backend lives in `backend/`, leaving room for a client

**Status:** accepted
**Date:** 2026-11-07

## Context

The backend (Django, django-ninja) sat at the repository root. A client app is coming, but
whether it is web or mobile, and whether it lives in this repo, is not decided yet.

## Decision

Move the backend into `backend/` (`src/`, `manage.py`, `pyproject.toml`, `uv.lock`,
`.env.example`, `.python-version`). Governance stays at the root: `AGENTS.md`, `specs/`,
`docs/`, `scripts/`, `.github/`, `deploy/` and the root `Makefile`, which remains the single
entry point and delegates with `uv --project backend`.

No `frontend/` directory is created until the client decision is made; that decision gets
its own ADR.

## Consequences

- Backend commands run from the root via `make`, or from inside `backend/`.
- Dependabot watches `/backend`.
- The spec gate guards `backend/src/`.
