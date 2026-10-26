# Rules for working in this repository

This is the only rules file. `CLAUDE.md` is a symlink to it, `.cursor/rules/main.mdc` points
at it, and `CONTRIBUTING.md` points at it. Claude, Cursor, Codex, and humans read the same
bytes, so the rules cannot drift apart. Edit this file and every agent is updated.

Read this before your first edit in a session.

---

## 0. Agents: check ponytail before your first edit

Every AI agent working here runs with [ponytail](https://github.com/DietrichGebert/ponytail)
loaded. It is how §1.9, smallest thing that works, gets applied edit by edit.

At the start of every session, before any edit:

- **Loaded** - any one of these is in your context: the `PONYTAIL MODE ACTIVE` banner (Claude
  Code, Codex, Cursor hooks), a `ponytail` skill such as `ponytail:ponytail`, or a rule titled
  "Ponytail, lazy senior dev mode" (Cursor and other rule-file installs). Follow it and carry
  on.
- **Not loaded** - stop. Tell the developer you are working for: *"ponytail is not loaded in
  this session, and this project expects every agent to use it. Install it (commands in
  AGENTS.md §0), or confirm you want to continue without it."* Then wait. Continue only on an
  explicit yes, and write `ponytail: not used, confirmed by the developer` in the PR's Author
  section.

| Agent | Install, then start a new session |
|---|---|
| Claude Code | `/plugin marketplace add DietrichGebert/ponytail`, then in a separate prompt `/plugin install ponytail@ponytail` |
| Codex | `codex plugin marketplace add DietrichGebert/ponytail` and `codex plugin add ponytail@ponytail`, then trust its hooks in `/hooks` |
| Cursor | `git clone https://github.com/DietrichGebert/ponytail` and `node ponytail/scripts/cursor-hooks.js install` |
| Any other | The matching rules file from the [ponytail install guide](https://github.com/DietrichGebert/ponytail#install) |

## 1. Non-negotiables

These hold for every change, by every author, human or agent. Changing one is an amendment:
a PR that edits this section, approved by a CODEOWNER, with the reason in the PR body. No
other PR may edit this section.

1. **Every spec serves a stated goal.** `docs/goals.md` holds them in priority order; a
   spec names its goal in front matter. Work that serves no goal there does not start.
2. **Code is authorised by a spec.** Anything under `backend/src/` or `frontend/src/` requires an approved spec that is
   already merged on `main`. See §2.
3. **The gates are absolute.** Every gate in §3 passes, or the PR does not merge. There is no
   warn-only tier and no bypass.
4. **Clinical data is the most sensitive thing we hold.** Session audio and transcripts,
   notes, records, journal entries, assessment results, and assistant conversations are
   clinical data. Never log it. Never send it to an LLM, an advertiser, an employer, or any
   other third party without the person's consent to that specific use. Never commit a fixture
   containing a real person. A child's data also needs a guardian's consent. A spec that
   stores anything about a person fills in its Data section and passes the privacy review in
   `docs/privacy-review.md`.
5. **Assume the database leaks.** Design every table as if a full dump were published tomorrow:
   it must reveal nothing about anyone. Clinical data and everything that identifies a person
   (name, phone, email, national ID, address) is encrypted by the application before it
   reaches Postgres, under keys that never live in the database, its backups, or the repo.
   Lookups on an encrypted field use a keyed hash (blind index), never plaintext. Disk or
   database-level encryption does not count: anyone who can query the database reads straight
   through it. The design is [ADR 0004](docs/adr/0004-assume-the-database-leaks.md).
6. **Consent is per use.** Accepting the terms is not consent to record a session, share a
   record, or refer a client. Each such use asks for its own consent, stores the version agreed
   and when, and can be withdrawn.
7. **AI drafts, a professional decides.** AI output is never stored as a clinical fact until a
   professional confirms it. An AI that talks to users never presents itself as a clinician or
   diagnoses, and does not ship without the crisis protocol: it detects risk of harm to self or
   others and hands over to a human.
8. **No dependency without a reason in writing.** New package means an ADR in `docs/adr/`
   naming what it does that the standard library and Django cannot.
9. **Smallest thing that works.** No interface with one implementation, no config for a value
   that never changes, no abstraction for a second case that does not exist yet.
10. **Agents do not edit their own guardrails.** The paths in `.github/CODEOWNERS` are
   CODEOWNER territory. Propose changes, never self-approve them.

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

**Waived for:** changes that touch no file under `backend/src/` or `frontend/src/`. Documentation, CI, tooling, and
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
| Spec gate | `make spec` | A spec's front matter or Data section is incomplete, or application code changed without a merged, approved spec |
| Security | `make sec` | A locked dependency has a known vulnerability, or git history holds a secret or personal data |
| Workflows | `make workflows` | A workflow is malformed, or has an unpinned action, excess permissions, or injection |

`print` is banned in application code (ruff `T20`); scripts are CLIs and may print. Fix a
security finding, do not suppress it - see [ADR 0003](docs/adr/0003-ci-security-tools.md).

**The file-length limit is a design rule, not a style rule.** A file over 300 lines is one an
agent reads in fragments and edits with half the context. Split by responsibility. Generated
migrations are exempt.

## 4. Layout and conventions

```
backend/src/config/         Django project: settings, urls, asgi. Not application code.
backend/src/config/settings/  base -> dev | test | prod. Secrets come from the environment.
backend/src/core/           The application package.
backend/src/core/tests/     Tests live beside the code they cover.
frontend/                   Frontend client application.
specs/                      One directory per spec. The authorisation record.
docs/goals.md               What the project is for, in priority order. Specs trace back to it.
docs/adr/                   Why a technical decision was made. Specs say what, ADRs say why.
docs/privacy-review.md      The checklist every change touching personal data passes.
scripts/                    The CI gates, as runnable Python. No logic hides in YAML.
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
2. Read `backend/src/core/api.py` - it is the reference for how an endpoint is shaped here.
3. Write the test first when the change has behaviour worth asserting.
4. Keep the diff to what the spec asks for. Found an unrelated problem? Say so in the PR body;
   do not fix it in the same PR.
5. Touching anything about a person - a model, migration, endpoint, log line, LLM call? Run
   [docs/privacy-review.md](docs/privacy-review.md) and put the result in the PR body.
6. Run `make ci`. Open the PR. Report honestly what passed and what you skipped.
