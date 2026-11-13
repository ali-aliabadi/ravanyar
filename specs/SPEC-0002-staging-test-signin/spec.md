---
id: SPEC-0002
title: Sign in on staging with test numbers, without SMS
status: draft   # draft | approved | implemented | superseded
goal: 1         # which goal in docs/goals.md this serves
data: none      # none | identifying | clinical - see AGENTS.md §1.4-§1.5
---

## Problem

Staging has no SMS provider key, so nobody can get past the sign-in code and test anything
built on SPEC-0001. Giving staging a real Kavenegar key would also mean testing with real
phone numbers.

## Outcome

On a pre-launch deployment, an operator lists a few invented phone numbers and one 6-digit
code in the server environment. Those numbers sign in with that code and no SMS is sent;
every other number behaves exactly as before. The web client shows a staging banner while
this is on. A deployment that is not marked pre-launch refuses to start with test numbers set.

## Scope

**In:** `RAVANYAR_TEST_PHONES` and `RAVANYAR_TEST_CODE` in production settings, allowed only
with `RAVANYAR_PRELAUNCH=1`; the fixed code for listed numbers in `request_code`; a warning
log line for every test code issued and every test sign-in; `test_mode` on `/api/health`;
the banner in the web client.

**Out:** any change to rate limits, attempt limits, consent, encryption, or the access log;
test numbers in dev or test settings; seed data (only SPEC-0001 features exist, and the
test sign-in itself creates the accounts and consents they need).

## Acceptance criteria

- [ ] Given test numbers and `RAVANYAR_PRELAUNCH` unset, when production settings load, then
  startup fails.
- [ ] Given test numbers and a code that is not 6 ASCII digits, when settings load, then
  startup fails.
- [ ] Given test mode, when a listed number requests a code, then no SMS is sent and the
  fixed code signs it in; a wrong code still counts as a failed attempt.
- [ ] Given test mode, when any other number requests a code, then it gets a real SMS and the
  fixed code does not sign it in.
- [ ] Given test mode is off, the listed numbers are ordinary numbers.
- [ ] Every test sign-in writes a log line with the account id and no phone number.

## Open questions

None.
