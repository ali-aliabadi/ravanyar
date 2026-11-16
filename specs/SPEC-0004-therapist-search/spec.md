---
id: SPEC-0004
title: Client search for approved therapists
status: approved   # draft | approved | implemented | superseded
goal: 1         # which goal in docs/goals.md this serves
data: identifying      # none | identifying | clinical - see AGENTS.md §1.4-§1.5
---

## Problem

Clients can sign up, and therapists can be approved (SPEC-0003), but a client has no way to
find an approved therapist. SPEC-0003 left that to this spec.

## Outcome

A signed-in client opens "find a therapist", types what they need (a name, a title, a
specialty such as اضطراب), and sees approved therapists with their title, specialties and
fee. Opening one shows the full public profile. A therapist who is not approved, or whose
account is deleted, never appears.

## Scope

**In:** a search endpoint over approved profiles (free text matched against name, title and
specialties, with Persian letter variants and half-spaces normalised; paginated); a
public-profile endpoint for one approved therapist; the client "find a therapist" screen in
the web client.

**Out:** booking, availability, payment (later specs); filters by fee, gender or city;
ranking; photos; ratings; search before sign-in.

## Acceptance criteria

- [ ] Given approved, draft, submitted and rejected profiles, when a client searches with no
  text, then only the approved ones come back.
- [ ] Given a search for a specialty, then profiles whose name, title or specialties contain
  it come back; Arabic ي/ك and a missing or extra half-space (ZWNJ) still match.
- [ ] Given an approved profile edited back into review, or a deleted therapist, then it is
  not found until approved again.
- [ ] Given a public-profile request for a therapist who is not approved, then 404, the same
  as an id that does not exist.
- [ ] Given no token, then 401 (default deny).
- [ ] The search text is sent in the request body, and no log line contains it.

## Data

- **Stored:** nothing new.
- **Encrypted:** nothing new. Search reads the published profile, which SPEC-0003 keeps as
  plaintext public data.
- **Consent:** none new. Search reads only what a therapist published to be found.
- **Retention:** search keeps nothing. The search text is never logged, since a search for
  "depression" says something about the person typing it.
- **Access:** any signed-in account with current consent reads approved profiles. As in
  SPEC-0003, public data writes no access-log row.
- **Sent outside:** nothing.

## Later: possible improvements for SPEC-0005

Noted while planning this spec. None of them block it.

- **Fixed specialty list.** Specialties are free text, so search depends on spelling. A fixed
  list (like `RejectReason`) gives exact filters.
- **Search at scale.** Substring matching scans every approved profile. That's fine for
  hundreds; move to Postgres full-text or trigram search when it isn't.
- **Search before sign-in.** Lets a client browse first, but makes the route public.

## Open questions

- Should a therapist or admin also be able to search? This spec allows any signed-in account
  with consent, since the data is public by design.
- Result order is newest approval first. A fairer order (rotation, availability) belongs with
  booking.
