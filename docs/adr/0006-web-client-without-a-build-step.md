# 6. The first client is a static web app with no build step

**Status:** accepted
**Date:** 2026-11-07

## Context

ADR 0005 left the client decision open. The backend has sign-in, consents and account
deletion; nothing else yet. The site is served at margin.alialiabadi.ir by the host's nginx,
which already proxies `/api/` to Django on the same origin.

## Decision

The client is plain HTML, CSS and JavaScript in `frontend/`: Persian, right-to-left, light
and dark. No framework, no npm, no bundler. nginx serves the folder as static files.

The font (Vazirmatn, OFL) is vendored in `frontend/fonts/` so no request leaves our origin.
A Content-Security-Policy allows only `'self'`, so there are no inline scripts or
third-party code that could read the session token.

## Consequences

- Zero dependencies to audit; deploying is copying a folder.
- No type checking or component reuse on the client. Revisit (and write a new ADR) when the
  client grows past a handful of screens, likely with booking.
- Consent document versions are duplicated in `frontend/app.js` until the API exposes them.
