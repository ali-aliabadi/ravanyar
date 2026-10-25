---
id: SPEC-0001
title: Accounts, per-person encryption, consent ledger, and central access control
status: draft   # draft | approved | implemented | superseded
goal: 1         # which goal in docs/goals.md this serves
data: identifying  # none | identifying | clinical - see AGENTS.md §1.4-§1.5
---

## Problem

Nobody can have an account yet, so none of Goal 1 can start. Every later Goal 1 feature
(verification, booking, the record, the session assistant) stores data about a person, and
each one would otherwise invent its own encryption, consent checks and access rules. Done
three times it is done wrong at least once. The foundation they all build on has to exist
first, and it has to be right on day one: the user model and the encryption layout are
expensive to change once real data is stored under them.

## Outcome

A person signs in with their Iranian mobile number and a one-time code sent by SMS, chooses
whether they are a client or a therapist, and accepts the terms and privacy policy. That
acceptance is recorded with the document version and the time it was given. Their phone
number is never stored in readable form: a full database dump shows only ciphertext and keyed
hashes. Every endpoint refuses anyone who is not signed in unless it is explicitly marked
public. Every read of a person's data goes through one access check that records who read
whose data, and why. A person can delete their account, and once they do the stored copy of
their phone number can no longer be decrypted.

## Scope

**In:**

- A custom user model (`Account`) in the first migration. It has a UUID primary key, a role
  (`client`, `therapist` or `admin`), and no plaintext identifying field. It has no password.
- Sign-in with phone and SMS code. Kavenegar's Verify Lookup API is called over HTTPS with
  the standard library. Only Iranian mobile numbers are accepted, and Persian and
  Arabic-Indic digits are normalised.
- At first sign-in the account is created, with role `client` or `therapist` chosen by the
  person. `admin` is never self-assigned and has no extra rights in this spec.
- Opaque bearer session tokens that expire after 30 days, plus logout.
- ADR 0004 envelope encryption: one data key per account, wrapped by a master key from the
  environment, and AES-256-GCM with (table, column, row id) as associated data. Also the HMAC
  blind index for phone lookups, and crypto-shredding on account deletion.
- A consent ledger that records each grant (document, version, time) and each withdrawal,
  with endpoints to list, grant and withdraw. The only documents in this spec are `terms` and
  `privacy`.
- One access-control service, `authorize(actor, subject, purpose)`. Decrypting a person's
  data requires the grant it returns, and every decision, allowed or denied, writes an
  access-log row. The only rule in this spec is that a person may read their own data.
- An append-only access log, enforced by the database.
- Default-deny authentication on the `NinjaAPI`, and a test that fails when a route has none.

**Out:**

- Therapist verification, admin powers, and any rule that lets one person read another's
  data. Those are SPEC-0002 and SPEC-0003; each adds its rule to `authorize`.
- Name, email, national ID, address, date of birth, profile photo: no field is stored until a
  spec needs it.
- Changing a phone number, holding more than one role on one account, and per-IP rate
  limiting (handled at the reverse proxy, see Open questions).
- Django admin. It is not installed, and this spec does not authorise adding it.
- Per-use consents such as recording, sharing or LLM use. The ledger supports them; the specs
  that introduce each use add its document.
- Master-key rotation, KMS, backups, and deployment.

## Acceptance criteria

Sign-in
- [ ] Given a mobile number written as `09XX XXX XXXX`, `+989XX...`, `989XX...`, or in
      Persian or Arabic-Indic digits, when it is normalised, then all forms give the same
      `+989XXXXXXXXX`. A non-mobile or non-Iranian number is rejected with 422. Test numbers
      are built at runtime, never written out whole, so the gitleaks phone rule stays clean.
- [ ] Given a valid phone, when a code is requested, then one SMS is sent through Kavenegar
      and the response is the same 202 body whether or not an account exists for that phone.
- [ ] Given a code was requested less than 60 seconds ago, or 5 codes in the last hour for the
      same phone, when another is requested, then it is refused with 429 and no SMS is sent.
- [ ] Given a code, when it is verified correctly within 2 minutes, then a session token is
      returned; when it is wrong 5 times, expired, or already used, then it is refused and
      that code can never succeed.
- [ ] Given a phone with no account, when its code is verified with a role and the current
      `terms` and `privacy` versions, then an account is created with that role and both
      consents are recorded. Sending role `admin` is rejected with 422.
- [ ] Given a session token, when the person logs out, then that token is refused with 401.
- [ ] Given a token older than 30 days, when it is used, then it is refused with 401.

Default deny
- [ ] Every operation in the OpenAPI schema requires auth, except `health`, `ready`,
      `request_code` and `verify_code`. A new route without auth fails the test.
- [ ] Given no token or an invalid one, when any non-public endpoint is called, then 401.

Encryption
- [ ] Given a value encrypted for row A, when its ciphertext is copied into row B or
      decrypted under another person's data key, then decryption fails.
- [ ] Given a seeded database, when every text, varchar, jsonb and bytea value in every table
      is scanned, then no form of any seeded phone number appears.
- [ ] Given the master key or the blind-index key is missing or not 32 bytes, when Django
      starts, then it refuses to start.

Consent
- [ ] Given an account, when it lists its consents, then it sees each grant with document,
      version, given time and withdrawn time.
- [ ] Given an account has withdrawn `terms` or `privacy`, or has not accepted its current
      version, when it calls any endpoint other than the consent endpoints, logout or account
      deletion, then it gets 403 `consent_required`.
- [ ] Given a withdrawn consent, when it is granted again, then a new ledger row is added and
      the old row keeps its withdrawal time.

Access control and log
- [ ] Given an account reads its own profile, then the phone is returned decrypted and an
      access-log row records actor, subject, purpose `profile`, and `allowed`.
- [ ] Given `authorize` is called with a different actor and subject, then it raises, no data
      is decrypted, and an access-log row records `denied`.
- [ ] Given an access-log row, when anything issues SQL `UPDATE` or `DELETE` on it, then the
      database rejects it.

Deletion
- [ ] Given an account, when it is deleted, then its wrapped data key, phone ciphertext and
      phone blind index are erased, its sessions are revoked, its pending codes are removed,
      and a stored copy of its phone ciphertext no longer decrypts.
- [ ] Given a deleted account's phone, when it signs in again, then a new, separate account is
      created.

## Data

- **Stored:** For each account: role, created and deleted times, phone number (identifying),
  wrapped data key. For each sign-in code: the phone's blind index, a keyed hash of the code,
  expiry, attempt count. For each session: the token's hash, expiry, revocation time. Consent
  ledger rows: account id, document, version, given time, withdrawn time. Access-log rows:
  actor id, subject id, purpose, decision, time. No name, email, national ID, IP address or
  user agent is stored anywhere.
- **Encrypted:** The phone is encrypted under the account's data key with AES-256-GCM, with
  associated data `core_account|phone|{account id}`. The data key is wrapped under the master
  key with associated data `{account id}`. The phone has an HMAC-SHA256 blind index on
  `Account` and on sign-in codes, under the blind-index key. The code is stored only as an
  HMAC under the same key. The session token is 256 random bits and stored only as its
  SHA-256; the token is high-entropy, so an unkeyed hash is enough. Both keys come from the
  environment, never the database or the repo.
- **Consent:** `terms` and `privacy`, each by version, are recorded at first sign-in and
  required for every endpoint except consent, logout and deletion. A withdrawal sets
  `withdrawn_at`; the account is then blocked (403 `consent_required`) until it grants the
  current version again or deletes itself. Until the real texts exist the versions are
  placeholders (`terms-draft-0`, `privacy-draft-0`), and real users must not sign up under
  them. Sending the phone to Kavenegar is how sign-in works, so it needs no separate consent;
  the privacy policy discloses it.
- **Retention:** An account's data is kept until the account is deleted. Deletion is
  crypto-shredding: the wrapped data key, phone ciphertext and blind index are set to NULL,
  and the row stays as an empty tombstone so access-log foreign keys hold. Sign-in codes are
  purged 24 hours after creation, and immediately when the account is deleted. Access-log and
  consent rows are kept; they hold only opaque IDs. Backups still hold the wrapped data key
  until they expire (see Open questions 1).
- **Access:** In this spec an account reads only its own phone and consents. No other person,
  admin included, can read them. Every `authorize` decision writes an access-log row,
  including self-reads and denials.
- **Sent outside:** For each code request, the normalised phone number and the 6-digit code
  go to Kavenegar over HTTPS. Nothing else leaves the app, and nothing goes to an LLM.
  Kavenegar's responses and errors are logged by status code only.

## Open questions

None of these blocks the acceptance criteria. Questions 1 to 3 block production launch.

1. **ADR 0004 overclaims crypto-shredding.** Its point 4 says deleting the data key reaches
   "backups we cannot rewrite". It does not: a backup taken before the deletion holds the
   wrapped data key, and the unchanged master key unwraps it. The fix needs a superseding ADR
   that either bounds backup retention (for example 30 days, after which the deletion is
   complete everywhere) or keeps wrapped keys out of the main backup set. This spec claims
   only what holds: immediate in the live database, complete once the last earlier backup
   expires.
2. **Consent texts.** The placeholder versions must be replaced by real `terms` and `privacy`
   texts, written and kept in the repo by version, before the first real user.
3. **Hosting and master-key location.** The keys are environment secrets for now (ADR 0004).
   Where the app is hosted decides the KMS and the data-residency position.
4. **SMS pumping.** The per-phone limits do not stop an attacker requesting codes for many
   different numbers, which costs money. Per-IP limits at the reverse proxy are needed before
   launch. They are not kept in the app, because an IP address is identifying data.
5. **Client app.** Bearer tokens were chosen because they work for both web and mobile. If the
   client is a web app, where it stores the token (XSS exposure) is decided with that app.
