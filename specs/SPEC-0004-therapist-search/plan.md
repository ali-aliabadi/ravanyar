---
id: SPEC-0004
---

## Approach

### 1. Specialty list: `core/models/practice.py`

- `Specialty(models.TextChoices)`, next to `RejectReason`, holds twelve codes:
  - anxiety, depression, couples, family
  - child, adolescent, trauma, addiction
  - sleep, ocd, grief, work_stress
- `TherapistProfile.specialties` becomes
  `ArrayField(CharField(choices=Specialty.choices), size=5, default=list, blank=True)`.
  `ArrayField` ships with Django, so there is no new dependency.
- Migration 0004 converts the old text in three steps:
  1. Add the new column.
  2. A data step maps text to codes, with Arabic letters and ZWNJ normalised. The mapping is
     frozen in the migration, so it cannot drift.
  3. Remove the old column and rename the new one.

  It writes directly, not through `update_profile`, so approved profiles stay approved.
- `verification.update_profile` keeps `specialties` among the public fields, so a change
  sends an approved profile back to review. `forget()` empties them.

### 2. Search: `core/search.py`, `core/api_search.py`

- **Base queryset:** `status=approved`, `account__is_active=True`, ordered by
  `-reviewed_at, pk` (nulls last) so pages stay stable.
- **`search(q, specialty)`:**
  - The specialty filters with `specialties__contains=[code]`.
  - The text is matched with `icontains` against `Concat(display_name, title)`. Arabic ي→ی
    and ك→ک, and ZWNJ removed, are applied on both sides via `Replace`, so there is no new
    column.
- **`public_profile(id)`:** returns the profile, or `NotFoundError` when it is unapproved or
  missing.
- **Routes:**
  - `POST /api/therapists/search` with body `{q ≤ 100, specialty?}`, paginated by ninja's
    `PageNumberPagination` (20 a page). POST keeps the search out of URLs, so out of nginx,
    uvicorn and Cloudflare logs.
  - `GET /api/therapists/{id}`.
  - `PublicProfileOut` has only `id`, `display_name`, `title`, `specialties`, `bio`,
    `fee_rial`.

### 3. Booking models: `core/models/booking.py`

- **`Slot`:**
  - Fields: `id`, `therapist` (FK `Account`, PROTECT), `start_at`, `withdrawn_at`,
    `created_at`.
  - An index on `(therapist, start_at)`.
  - A slot is withdrawn, never deleted, because bookings point at it.
- **`Booking`:**
  - Fields: `id`, `slot` (FK, PROTECT), `client` (FK `Account`, PROTECT), `status`
    (`booked`/`cancelled`), `cancelled_by` (`client`/`therapist`/`system`), `created_at`,
    `cancelled_at`.
  - `UniqueConstraint(fields=["slot"], condition=Q(status="booked"))` is the
    double-booking guarantee, held by Postgres, not by a check-then-insert.

### 4. Booking services: `core/booking.py`

- **Constants:** 50-minute sessions, a one-hour lead, a 60-day horizon. They are module
  constants, not settings (AGENTS.md §1.9).
- **`add_slot`:**
  - Requires the therapist role and an approved profile, otherwise 409.
  - Checks the time window.
  - Locks the profile row and refuses a start within 50 minutes of another live slot, so one
    therapist's concurrent adds serialise.
- **`remove_slot`:** only for an unbooked slot of their own; the slot is withdrawn.
- **`open_slots`:** 404 unless the therapist is approved, then future, unwithdrawn,
  unbooked slots at least an hour ahead.
- **`book`:**
  - Requires the client role.
  - Locks the open slot (`select_for_update(of=self)`) and creates the booking.
  - An `IntegrityError` from the constraint becomes 409.
- **Cancelling:**
  - `cancel_as_client`: own booking, before the start; the slot reopens because it has no
    active booking left.
  - `cancel_as_therapist`: own booked slot, before the start; cancels the booking and
    withdraws the slot.
- **Lists:**
  - `my_bookings(client)`: the client's own bookings.
  - `my_slots(therapist)`: annotated `open`/`booked`/`cancelled`, never with the client.
- **`forget(account)`:** called from `services.delete_account`; cancels future bookings on
  either side (`system`) and withdraws future slots.

### 5. Booking API: `core/api_booking.py`, default `consented` auth

| Route | Who |
|---|---|
| `GET /therapists/{id}/slots` | any signed-in account |
| `POST /bookings` `{slot_id}` → 201 | client |
| `GET /me/bookings` | client |
| `POST /bookings/{id}/cancel` | client |
| `GET /therapist/slots` | therapist |
| `POST /therapist/slots` `{start_at}` → 201 | therapist |
| `DELETE /therapist/slots/{id}` → 204 | therapist |
| `POST /therapist/slots/{id}/cancel` | therapist |

`start_at` is an aware datetime (`AwareDatetime`); a naive one is 422. A bad time is the new
`bad_time` error (422).

### 6. Web

- **`lib.js`:**
  - `SPECIALTIES` labels and `specialtyNames`.
  - Tehran-time helpers: `faDay`, `faTime`, `tehranDay`, `byDay`, and `tehranIso`, which
    builds the instant using the offset `Intl` reports (`longOffset`), not a hard-coded one.
  - The `bad_time` message.
- **`client.js`:**
  - Search with a specialty select.
  - The profile lists free times by day and books after a confirm.
  - A "نوبت‌های من" tab lists upcoming bookings (with cancel) and past or cancelled ones.
- **`therapist.js`:**
  - Specialty checkboxes, capped at five.
  - A "زمان‌های من" tab: a Jalali week picker (seven day buttons, previous and next weeks up
    to the horizon) and a time select from 06:00 to 23:30 in 30-minute steps; then the slots
    by day with remove or cancel. `<input type="date">` is not used because it shows a
    Gregorian picker.
- **`admin.js`:** specialty labels.

### 7. Seed

- Specialty codes for the invented therapists, plus one draft therapist.
- Each approved one gets slots at 10:00 and 17:00 Tehran time for the next seven days, with
  ids derived from therapist, day and hour so re-running adds only new days.
- The seed uses a fixed +03:30 offset: the slim image has no tz database, and Iran has had no
  daylight saving since 2022.

## Alternatives rejected

- **Search with `GET ?q=`:** the search text would land in every access log on the way.
- **A normalised copy of each searchable field:** a migration and a backfill to save a
  `Replace` on a few hundred rows.
- **A `Specialty` table with a many-to-many relation:** a join and an admin-managed table to
  hold twelve fixed values.
- **Keeping the free text beside the codes:** two sources for one fact.
- **A Postgres exclusion constraint for slot overlap:** needs `btree_gist`. Overlap is one
  therapist's own calendar, and a row lock suffices. Double booking crosses clients, so the
  database holds that one.
- **Recurring availability rules:** a rule engine nobody has asked for.
- **A calendar library:** a dependency and an ADR, when `fa-IR` already formats in Jalali.

## Risks

- **No payment, so bookings are free and confirm at once.** One client could hold many
  slots. Pre-launch data is invented; a per-client cap (see Later) is the guard before real
  users.
- **The specialty conversion is lossy:** text the map does not recognise is dropped. On
  pre-launch data that text is invented.
- **Time zones:** the browser sends instants built from a Tehran-time input, and display
  goes through `Intl` with `Asia/Tehran`, so it stays right if Iran's rules change.
