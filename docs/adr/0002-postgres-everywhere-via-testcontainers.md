# 2. Postgres everywhere, provided by testcontainers in tests

**Status:** accepted
**Date:** 2026-09-21

## Context

SQLite in tests and Postgres in production is the cheapest way to make a test suite lie.
Constraints, transactions, JSON behaviour, and migration semantics all differ.

## Decision

Postgres is the only database, in development, CI, and production. Integration tests receive a
real Postgres container from testcontainers, created and destroyed per session. Unit tests
touch no database at all and are marked `unit`.

## Consequences

Integration tests need a running Docker daemon, locally and in CI, and are slower than a
SQLite suite. The unit/integration split keeps the fast feedback loop fast.
