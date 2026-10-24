---
id: SPEC-NNNN
title: <short imperative title>
status: draft   # draft | approved | implemented | superseded
goal: 1         # which goal in docs/goals.md this serves
data: none      # none | identifying | clinical - see AGENTS.md §1.4-§1.5
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

Required unless `data: none`; `make spec` fails while any field below is empty or still holds
a `<placeholder>`. Run [docs/privacy-review.md](../../docs/privacy-review.md) on the design.

- **Stored:** <which fields, about whom, identifying or clinical>
- **Encrypted:** <which fields under the person's data key; which have a blind index (ADR 0004)>
- **Consent:** <which consent covers each use, which version; what happens when withdrawn>
- **Retention:** <how long; deleted by shredding the data key, or how>
- **Access:** <who can read it; which reads write to the access log>
- **Sent outside:** <exactly what goes to an LLM or any third party, or "nothing">

## Open questions

Anything unresolved. A spec may be approved with open questions if they do not block the
acceptance criteria.
