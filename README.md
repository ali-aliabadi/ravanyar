# core

[![ci](https://github.com/ali-aliabadi/ravanyar/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ali-aliabadi/ravanyar/actions/workflows/ci.yml)

Backend for a personalised education platform: a study helper for students, built for schools,
with room for alternative learning paths.

What the project is for is written down in [docs/goals.md](./docs/goals.md), in priority
order. The product direction is deliberately undecided. What is decided is how the work happens -
every change is authorised by a merged spec, and the CI gates hold the line. Read
[AGENTS.md](./AGENTS.md); it is the whole rulebook, for people and for coding agents alike.

## Requirements

Python 3.13, [uv](https://docs.astral.sh/uv/), Docker (for the local database and for
integration tests).

## Start

```bash
make install            # create the venv from the lockfile
docker compose up -d db # local Postgres
make migrate
make run                # http://localhost:8000/api/docs
```

## Working here

```bash
make ci     # every gate CI enforces - run before opening a PR
make format # fix what is auto-fixable
make help   # all targets
```

A change to `src/` needs an approved spec merged on `main` first. Copy `specs/TEMPLATE/` to
`specs/SPEC-0001-your-slug/`, open that as its own PR, then implement it in a second PR whose
branch name carries the spec id. The full rules are in [AGENTS.md](./AGENTS.md).

## Layout

| Path | What lives there |
|---|---|
| `src/config/` | Django project: settings, urls, ASGI entry point |
| `src/core/` | The application |
| `specs/` | One directory per spec - the authorisation record |
| `docs/adr/` | Why a technical decision was made |
| `docs/goals.md` | What the project is for, in priority order |
| `scripts/` | The CI gates, as runnable Python |

## One-time GitHub setup

Branch protection cannot live in a committed file. After pushing the repo:

```bash
scripts/protect.sh <owner>/<repo>   # needs the gh CLI and admin rights
```
