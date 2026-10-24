# 1. Record architecture decisions

**Status:** accepted
**Date:** 2026-09-21

## Context

Specs record what to build and why it matters to a user. They are a poor home for technical
choices - which database, which HTTP layer, which dependency - because those outlive the
feature that prompted them, and the next agent needs the reasoning, not the outcome.

## Decision

Technical decisions are recorded as short ADRs in `docs/adr/`, numbered sequentially. An ADR
is required for a new dependency (AGENTS.md §1.8) and for anything that binds the codebase
long-term. An ADR is never edited once accepted; it is superseded by a later one.

## Consequences

Some duplication between a spec's `plan.md` and an ADR. Accepted: the plan is about one
feature, the ADR is about the codebase.
