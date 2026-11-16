---
id: SPEC-0004
title: Find a verified therapist and book a session
status: approved   # draft | approved | implemented | superseded
goal: 1         # which goal in docs/goals.md this serves
data: identifying      # none | identifying | clinical - see AGENTS.md §1.4-§1.5
---

## Problem

Clients can sign up, and therapists can be approved (SPEC-0003), but a client has no way to
find an approved therapist or reserve time with one. SPEC-0003 left search to this spec.
Goal 1 says a client "finds a therapist whose identity and credentials are verified, books
... a session", and that "no slot can be booked twice". This is feature 2 of the product
document (رزرو و جلسات), Phase 1, without payment.

## Outcome

- **Finding.** A signed-in client opens "find a therapist", picks a specialty from a fixed
  list and/or types a name or title, and sees approved therapists with their title,
  specialties and fee. A therapist who is not approved, or whose account is deleted, never
  appears.
- **Publishing times.** An approved therapist chooses up to five specialties from the list
  and publishes the times they are free, using a Jalali week picker.
- **Booking.** On a therapist's profile the client sees the open times in Tehran time and
  books one. It is theirs and nobody else can take it, even if two clients press "book" at
  the same moment.
- **After booking.** Both sides see the booking, and either can cancel it before it starts.

## Scope

**In:**

- **Search:**
  - A search endpoint over approved profiles: free text matched against name and title, with
    Persian letter variants and half-spaces normalised, plus an optional specialty. It is
    paginated, and the text and specialty are sent in the body.
  - A public-profile endpoint for one approved therapist.
- **Specialties:**
  - A fixed list of twelve, stored as codes; a therapist chooses 0-5 of them.
  - Existing free-text specialties are converted to codes where they clearly match one.
- **Availability:**
  - An approved therapist adds open slots of one session each (50 minutes) in the next 60
    days, never overlapping each other.
  - They can remove a slot nobody booked.
- **Booking:**
  - A client books an open slot of an approved therapist, starting at least one hour from
    now. A slot holds at most one active booking, enforced by the database.
  - The client cancels before the start, and the slot opens again. The therapist cancels
    before the start, and the slot is withdrawn.
- **Lists:**
  - The client sees their bookings (therapist, time, status).
  - The therapist sees their slots, each open, booked or cancelled, with no client
    information.
- **Account deletion** blanks a therapist's published profile and specialties (SPEC-0003),
  cancels the person's future bookings, and withdraws a therapist's future slots.
- **Web:**
  - The client gets a "یافتن درمانگر" tab (search, results, profile with free times and
    booking) and a "نوبت‌های من" tab.
  - The therapist gets specialty checkboxes on the profile and a "زمان‌های من" tab with a
    Jalali week picker built from the browser's `fa-IR` formatting. There is no calendar
    library (ADR 0006).
  - The admin review screen shows specialty labels.
- **Staging seed:** one draft therapist, to show the approved-only filter, and open slots for
  the invented approved therapists.

**Out:**

- **Payment.** It is not planned. Booking confirms at once (see Risks).
- **Online sessions** (video or audio).
- **Reminders and notifications.**
- **Moving a booking** to another time (cancel and book again).
- **Recurring weekly availability.**
- **No-show handling.**
- **Search:** search before sign-in; filters by fee, gender or city; ranking; photos;
  ratings; full-text or trigram search.
- **Specialties:** therapists proposing new ones (Phase 3 referral work).
- **Showing the client's identity to the therapist.**
- **Workshop booking** (feature 9). The booking table has nothing session-specific, so
  workshops can reuse it.

## Acceptance criteria

Search and specialties:

- [ ] Given approved, draft, submitted and rejected profiles, when a client searches with
  nothing, then only the approved ones of active accounts come back.
- [ ] Given a search for a name or title, then Arabic ي/ك and a missing or extra half-space
  (ZWNJ) still match.
- [ ] Given a search with a specialty, then only approved therapists who chose it come back;
  with text as well, both must match. A code not on the list is 422, and the code is not
  echoed back.
- [ ] Given an approved profile edited back into review, or a deleted therapist, then it is
  not found until approved again.
- [ ] Given a public-profile request for a therapist who is not approved, then 404, the same
  as an id that does not exist.
- [ ] Given a profile update with a specialty code not on the list, or more than five, then
  422; changing the specialties of an approved profile sends it back to review.
- [ ] Given the migration, then "اضطراب" and its Arabic-letter and half-space variants become
  `anxiety`; text that matches no code is dropped, and the profile stays in its state.
- [ ] The search text and specialty are sent in the body, and no log line contains them.

Booking:

- [ ] Given an approved therapist, when they add a slot 3 days ahead, then it is open; a slot
  in the past, more than 60 days ahead, or overlapping one of theirs is 422. A therapist who
  is not approved gets 409.
- [ ] Given a client, when they list an approved therapist's slots, then only open slots
  starting at least one hour from now come back; a therapist who is not approved shows 404.
- [ ] Given two bookings of the same slot, then exactly one succeeds and the other is 409; the
  database refuses a second active booking even if both passed the open-slot check.
- [ ] Given a client who cancels before the start, then the slot is open again; after the
  start, cancelling is 409.
- [ ] Given a therapist who cancels a booked slot, then the booking shows cancelled by the
  therapist and the slot is not offered again.
- [ ] Given a therapist calling client booking routes, or a client calling therapist slot
  routes, then 403; one client cannot see or cancel another's booking (404).
- [ ] Given a deleted client, their future bookings are cancelled and the slots open again;
  given a deleted therapist, their future bookings are cancelled and their slots withdrawn.
- [ ] No response to a therapist contains a client's id or phone.
- [ ] Given no token, then 401 on every new route (default deny).

## Data

- **Stored:** specialty codes on the published profile (public), slots, and bookings; ids,
  times and enums only.
  - Slots: therapist account, start time, and whether withdrawn. This is the therapist's
    published availability.
  - Bookings: slot, client account, status, who cancelled, and timestamps. A booking links a
    client account to a therapist, which says a person is in therapy, so it is treated as
    identifying even though no column names anyone.
- **Encrypted:** nothing new. Search reads the published profile, which SPEC-0003 keeps as
  plaintext public data. Under ADR 0004 a booking row shows "account X booked therapist Y at
  T". X is a random UUID whose phone is ciphertext under X's own data key, so the dump names
  nobody.
- **Consent:** none new. Search reads only what a therapist published to be found. Booking is
  the service the terms cover (SPEC-0001); it is not recording, sharing a record, or
  referring (AGENTS.md §1.6).
- **Retention:** search keeps nothing; bookings stay while the accounts exist, and deletion
  cancels future bookings.
  - The search text and specialty are never logged, since a search for "depression" says
    something about the person typing it.
  - Deleting a client shreds their key (SPEC-0001), so past bookings point at a tombstone and
    identify nobody.
- **Access:** any signed-in account with consent reads approved profiles and open slots; each
  side reads only its own bookings or slots; the therapist never sees who booked. No route
  decrypts anything, so no access-log rows are added.
- **Sent outside:** nothing.

## Later: possible improvements

- **A per-client booking cap** (for example 2 upcoming sessions with one therapist, 4 in all).
  Without payment, nothing stops one client from holding many slots.
- **Recurring weekly availability** ("Saturdays 16-20"), expanded into slots, and **moving a
  booking** in one step.
- **Per-therapist session length.** It is fixed at 50 minutes today.
- **Specialty labels from the API** (`GET /api/specialties`) once a second client exists.
- **Search before sign-in**, and **Postgres full-text or trigram search** when substring
  matching on approved profiles gets slow.
- **Reuse for workshops** (feature 9): a capacity above one per slot.

## Open questions

- **What does the therapist see about who booked?** Accounts hold only an encrypted phone. A
  first name chosen by the client, encrypted under their key and read through `authorize()`
  with an access-log row, fits ADR 0004. It belongs with online sessions.
- **Is the specialty list right?** It should be reviewed by a clinician before launch. Any
  change to the list ships as a small migration that does not touch the data.
- **Are the numbers right?** Five specialties, 50-minute sessions, booking at least one hour
  ahead, and slots up to 60 days out are defaults to confirm.
- **Who can search?** Any signed-in account with consent can search, since the data is public
  by design. Results are ordered by newest approval first; a fairer order belongs with
  availability ranking.
