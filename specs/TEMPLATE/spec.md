---
id: SPEC-NNNN
title: <short imperative title>
status: draft   # draft | approved | implemented | superseded
goal: 1         # which goal in docs/goals.md this serves
---

## Problem

What is wrong or missing today, for whom. No solution here.

## Outcome

What is true once this ships, in one paragraph a non-engineer can check.

## Scope

**In:** the behaviour this spec authorises.

**Out:** the adjacent things it deliberately does not authorise. Be explicit - this list is
what a reviewer points at when a PR grows.

## Acceptance criteria

Each line becomes a test. Name the test in `tasks.md`.

- [ ] Given <state>, when <action>, then <observable result>.
- [ ] ...

## Data

Delete this section only if the change stores nothing about a person.

- **Stored:** which fields, about whom.
- **Retention:** how long, deleted how.
- **Access:** who can read it.
- **Sent to an LLM:** exactly what, or "nothing".

## Open questions

Anything unresolved. A spec may be approved with open questions if they do not block the
acceptance criteria.
