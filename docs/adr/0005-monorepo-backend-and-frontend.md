# 5. Monorepo structure with backend and frontend

**Status:** accepted
**Date:** 2026-10-26

## Context

Ravanyar requires both a backend (Django/Ninja API) and a frontend client (web application).
Previously, the backend application code, dependencies, and configuration lived at the
repository root (`src/`, `manage.py`, `pyproject.toml`, `uv.lock`).

Keeping the backend at the root makes adding a frontend awkward, requiring either a separate
repository (which complicates shared contracts, specs, and atomic changes) or an asymmetric
layout where the backend owns the root and the frontend is an afterthought in a subfolder.

## Decision

Structure the repository as a monorepo with top-level `backend/` and `frontend/` directories:

1. **`backend/`** holds all backend application code, configuration, and dependencies:
   `backend/src/` (Django configuration and core app), `backend/manage.py`,
   `backend/pyproject.toml`, `backend/uv.lock`, and `backend/.env.example`.
2. **`frontend/`** is established at the root to house the frontend client codebase.
3. **Repository root** retains project-wide governance and orchestration:
   `AGENTS.md`, `specs/`, `docs/`, `scripts/`, `.github/`, and the root `Makefile`.
   The root `Makefile` remains the single entry point for development and CI (`make ci`,
   `make run`, `make test`, etc.), delegating to `backend/` via `uv --project backend`.
4. **Spec gate (`scripts/check_spec.py`)** guards application code under both `backend/src/`
   and `frontend/src/`, allowing pure file moves and tooling updates as ordinary PRs while
   requiring approved specs for application changes.

## Consequences

- Backend commands run from the root using `--project backend` or from within `backend/`.
- Dependabot monitors dependencies in `/backend` rather than root `/`.
- Both frontend and backend share the same specification lifecycle (`specs/`), architectural
  decisions (`docs/adr/`), privacy standards, and linear git history.
