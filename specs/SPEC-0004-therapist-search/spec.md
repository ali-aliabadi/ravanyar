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
  - **Weekly repeat:** one request adds the same time on each of 1-8 weeks. Weeks that overlap
    another slot or pass the horizon are skipped and counted.
- **Booking:**
  - A client books an open slot of an approved therapist, starting at least one hour from
    now. A slot holds at most one active booking, enforced by the database.
  - The client cancels before the start, and the slot opens again. The therapist cancels
    before the start, and the slot is withdrawn.
  - **Moving:** the client moves a future booking to another open slot of the same therapist
    in one step. The new slot is booked and the old booking becomes `moved`, or nothing
    changes, so the old time is never lost to a race.
- **Lists:**
  - The client sees their bookings (therapist, time, status).
  - The therapist sees their slots, each open, booked or cancelled. They never see the
    client's id or phone; they see a booked client's first name only if the client chose to
    give one.
- **Client first name:**
  - Optional, up to 40 characters, set from "نوبت‌های من".
  - Encrypted under the client's data key (ADR 0004).
  - A therapist can read it only while that client has an active booking with them. The read
    goes through `authorize()` under a new `booking` purpose, and each one writes an
    access-log row.
- **Session reminders:**
  - About a day before a booked session, the client gets an SMS through the same path as the
    sign-in code: Kavenegar for real numbers, and for a staging test number no SMS but a log
    line (SPEC-0002).
  - The SMS carries a weekday and a time only.
  - `manage.py send_reminders` runs every 10 minutes in the deploy stack and reminds each
    booking once. The phone is read through `authorize()` under a new `reminder` purpose, and
    each read is logged.
- **Account deletion** blanks a therapist's published profile and specialties (SPEC-0003),
  cancels the person's future bookings, and withdraws a therapist's future slots.
- **Web:**
  - The client gets a "یافتن درمانگر" tab (search, results, profile with free times and
    booking) and a "نوبت‌های من" tab (upcoming with move and cancel, history, and the first
    name).
  - The therapist gets specialty checkboxes on the profile and a "زمان‌های من" tab with a
    Jalali week picker built from the browser's `fa-IR` formatting, with a weekly-repeat
    choice and the booked client's first name. There is no calendar library (ADR 0006).
  - The admin review screen shows specialty labels.
- **Staging seed:** one draft therapist, to show the approved-only filter, and open slots for
  the invented approved therapists.

**Out:**

- **Payment.** It comes in a later spec. Until then a booking confirms at once.
- **Online sessions** (video or audio).
- **Other notifications:** reminders to therapists, and change or cancellation messages.
- **Moving a booking to another therapist** (cancel and book).
- **No-show handling.**
- **Search:** search before sign-in; filters by fee, gender or city; ranking; photos;
  ratings; full-text or trigram search.
- **Specialties:** therapists proposing new ones (Phase 3 referral work).
- **Showing the therapist anything more than a client's chosen first name.**
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
- [ ] Given a client who moves a booking to an open slot of the same therapist, then the new
  slot is booked and the old booking is `moved`, and the old slot is open again. Given a
  taken slot, then 409 and the old booking is unchanged.
- [ ] Given a weekly request for 4 weeks where one week is taken, then 3 slots are created and
  1 is skipped. More than 8 weeks, or no week fitting, is 422.
- [ ] Given a client with a first name and an active booking, then the therapist's slot list
  shows the name, and an allowed `booking` access-log row is written. After the booking is
  cancelled the name is not shown. The stored name is ciphertext, and deleting the account
  removes it.
- [ ] Given bookings starting within 24 hours, when `send_reminders` runs, then a real number
  gets one SMS with a weekday and a time, and a staging test number gets a log line and no
  SMS. Each phone read writes a `reminder` access-log row, running again sends nothing more,
  and a session 3 days out is not reminded.
- [ ] Given no token, then 401 on every new route (default deny).

## Data

- **Stored:** specialty codes on the published profile (public); slots and bookings (ids,
  times, enums, and when reminded); a client's optional first name, encrypted.
  - Slots: therapist account, start time, and whether withdrawn. This is the therapist's
    published availability.
  - Bookings: slot, client account, status, who cancelled, and timestamps. A booking links a
    client account to a therapist, which says a person is in therapy, so it is treated as
    identifying even though no column names anyone.
- **Encrypted:** the client's first name, under their data key with the row location as
  associated data, like the phone. Search reads the published profile, which SPEC-0003 keeps
  as plaintext public data. Under ADR 0004 a booking row shows "account X booked therapist Y at
  T". X is a random UUID whose phone is ciphertext under X's own data key, so the dump names
  nobody.
- **Consent:** none new. Search reads only what a therapist published to be found. Booking and
  reminders about it are the service the terms cover (SPEC-0001); neither is recording,
  sharing a record, or referring (AGENTS.md §1.6). The first name is the client's own
  choice, given next to a sentence saying who sees it, and clearing it stops the sharing.
- **Retention:** search keeps nothing; bookings stay while the accounts exist, and deletion
  cancels future bookings.
  - The search text and specialty are never logged, since a search for "depression" says
    something about the person typing it.
  - Deleting a client shreds their key (SPEC-0001) and drops the first-name ciphertext, so
    past bookings point at a tombstone and identify nobody.
- **Access:** any signed-in account with consent reads approved profiles and open slots; each
  side reads only its own bookings or slots.
  - A therapist reads a client's first name only while the client is booked with them
    (`booking` purpose, access-logged).
  - The reminder job reads the client's phone (`reminder` purpose, access-logged).
- **Sent outside:** to Kavenegar, for a reminder, the client's phone number, a weekday and a
  time. That is the same provider and path as the sign-in code. The reminder template
  (`KAVENEGAR_REMINDER_TEMPLATE`, set in the Kavenegar panel) must not mention therapy or the
  therapist, so a lock screen shows nothing sensitive (privacy review §2).

## Later: possible improvements

- **Payment** (feature 2): a pay step between holding a slot and confirming it, which also
  ends free holds.
- **Reminders to therapists**, and messages when a session is cancelled or moved.
- **Per-therapist session length.** It is fixed at 50 minutes today.
- **Specialty labels from the API** (`GET /api/specialties`) once a second client exists.
- **Search before sign-in**, and **Postgres full-text or trigram search** when substring
  matching on approved profiles gets slow.
- **Reuse for workshops** (feature 9): a capacity above one per slot.

## Open questions

- **Reminder template text.** It needs to be created in the Kavenegar panel. Suggested:
  "روان‌یار: یادآوری قرار شما %token% ساعت %token2%." It says nothing about therapy.
- **Is the specialty list right?** It should be reviewed by a clinician before launch. Any
  change to the list ships as a small migration that does not touch the data.
- **Are the numbers right?** Five specialties, 50-minute sessions, booking at least one hour
  ahead, and slots up to 60 days out are defaults to confirm.
- **Who can search?** Any signed-in account with consent can search, since the data is public
  by design. Results are ordered by newest approval first; a fairer order belongs with
  availability ranking.
