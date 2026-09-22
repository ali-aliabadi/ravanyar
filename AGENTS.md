# Rules for working in this repository

This is the only rules file. `CLAUDE.md` is a symlink to it, `.cursor/rules/main.mdc` points
at it, and `CONTRIBUTING.md` points at it. Claude, Cursor, Codex, and humans read the same
bytes, so the rules cannot drift apart. Edit this file and every agent is updated.

Read this before your first edit in a session.

---

## 1. Non-negotiables

These hold for every change, by every author, human or agent. Changing one is an amendment:
a PR that edits this section, approved by a CODEOWNER, with the reason in the PR body. No
other PR may edit this section.

1. **Every spec serves a stated goal.** `docs/goals.md` holds them in priority order; a
   spec names its goal in front matter. Work that serves no goal there does not start.
1. **Code is authorised by a spec.** Anything under `src/` requires an approved spec that is
   already merged on `main`. See §2.
2. **The gates are absolute.** Lint, types, tests, file length, and the spec gate all pass, or
   the PR does not merge. There is no warn-only tier and no bypass.
3. **Student data is minors' data.** Never log it, never put raw personal data in an LLM
   prompt, never commit a fixture containing a real person. A spec that handles student data
   states explicitly what is stored, for how long, and who can read it.
4. **No dependency without a reason in writing.** New package means an ADR in `docs/adr/`
   naming what it does that the standard library and Django cannot.
5. **Smallest thing that works.** No interface with one implementation, no config for a value
   that never changes, no abstraction for a second case that does not exist yet.
6. **Agents do not edit their own guardrails.** `AGENTS.md`, `.github/`, `Makefile`, and
   `scripts/` are CODEOWNER territory. Propose changes, never self-approve them.

## 2. The workflow: a spec merges before its code

Two pull requests, in order. This is the rule referred to by "no MR other than this".

**PR 1 - the spec.** Branch `spec/SPEC-NNNN-short-slug`. Copy `specs/TEMPLATE/` to
`specs/SPEC-NNNN-short-slug/`, fill in `spec.md`, `plan.md`, and `tasks.md`, open the PR. A
human reviews the intent and sets `status: approved`. Merge.

**PR 2 - the implementation.** Branch `feat/SPEC-NNNN-short-slug`. Write the code. CI reads
the spec id out of your branch name, confirms that spec is merged and approved on `main`, and
rejects the PR otherwise.

An implementation PR cannot carry its own spec. That is the point: the authorisation exists,
reviewed by a human, before any code is written against it.

**Waived for:** changes that touch no file under `src/`. Documentation, CI, tooling, and
dependency bumps merge as a single ordinary PR.

**Spec lifecycle:** `draft` -> `approved` -> `implemented` -> `superseded`. The field lives in
the spec's front matter. The implementation PR flips `approved` to `implemented`.

**Spec ids** are zero-padded and never reused: `SPEC-0001`, `SPEC-0002`. Take the next free
number in `specs/`.

## 3. The gates

Run `make ci` before you open any PR. It runs exactly what GitHub runs.

| Gate | Command | Fails when |
|---|---|---|
| Lint + format | `make lint` | Ruff finds a violation, or code is unformatted |
| File length | `make lines` | A `.py` file exceeds 300 lines, or 500 in a test |
| Types | `make typecheck` | `mypy --strict` finds an error |
| Unit tests | `make test-unit` | Any test marked `unit` fails |
| Integration tests | `make test-integration` | Any test marked `integration` fails |
| Spec gate | `make spec` | `src/` changed without a merged, approved spec |

**The file-length limit is a design rule, not a style rule.** A file over 300 lines is one an
agent reads in fragments and edits with half the context. Split by responsibility. Generated
migrations are exempt.

## 4. Layout and conventions

```
src/config/         Django project: settings, urls, asgi. Not application code.
src/config/settings/  base -> dev | test | prod. Secrets come from the environment.
src/core/           The application package.
src/core/tests/     Tests live beside the code they cover.
specs/              One directory per spec. The authorisation record.
docs/goals.md       What the project is for, in priority order. Specs trace back to it.
docs/adr/           Why a technical decision was made. Specs say what, ADRs say why.
scripts/            The CI gates, as runnable Python. No logic hides in YAML.
```

- **Views are thin.** An endpoint validates input, calls one function, returns a schema.
  Business logic goes in a `services.py` module, never in a view or a model method.
- **Models are persistence.** Fields, constraints, and `Meta`. Behaviour lives in services.
- **Every endpoint is typed.** django-ninja schemas in, schemas out. `mypy --strict` has no
  opt-out; a genuine escape needs `# type: ignore[code]` plus a comment saying why.
- **Two kinds of test, marked explicitly.** `@pytest.mark.unit` touches no database and runs in
  milliseconds. `@pytest.mark.integration` gets a real Postgres from testcontainers - the same
  engine as production, so nothing passes in CI that fails in prod. An unmarked test fails the
  strict-marker check.
- **Async where it pays.** The app is served over ASGI. Views stay synchronous until one
  genuinely needs streaming or concurrency.

## 5. Commands

```bash
make install            # uv sync - create the venv from the lockfile
make run                # serve on http://localhost:8000/api/docs
docker compose up -d db # local Postgres for `make run`
make ci                 # every gate, in CI's order - run before every PR
make format             # fix what is auto-fixable
```

`make test-integration` needs a running Docker daemon; testcontainers starts and disposes of
Postgres itself. Never point a test at a database you care about.

## 6. Writing a change

1. Read the spec you are implementing, in full, before editing.
2. Read `src/core/api.py` - it is the reference for how an endpoint is shaped here.
3. Write the test first when the change has behaviour worth asserting.
4. Keep the diff to what the spec asks for. Found an unrelated problem? Say so in the PR body;
   do not fix it in the same PR.
5. Run `make ci`. Open the PR. Report honestly what passed and what you skipped.
