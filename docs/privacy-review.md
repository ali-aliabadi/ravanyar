# Privacy review

Run this before opening a PR that touches models, migrations, an endpoint, logging,
settings, an LLM call, or a third-party integration - and on every spec whose `Data` section
is not empty. Any author runs it, human or agent.

Review the diff (`git diff main...HEAD`), then read every file it touches in full. Report each
finding as `file:line`, severity (critical / high / medium / low), and the fix. Critical and
high are fixed before the PR opens. The rules behind this list are AGENTS.md §1.4-§1.7 and
[ADR 0004](adr/0004-assume-the-database-leaks.md).

## 1. The leak test (start here)

Imagine `pg_dump` of this branch's schema, filled with real data, published today.

- [ ] Every new column is one of: opaque ID, foreign key, timestamp, enum, amount, public data.
      Anything else is identifying or clinical, and is encrypted by the application.
- [ ] Encrypted fields use the person's data key with the row location as associated data;
      nothing is encrypted under a shared or hard-coded key.
- [ ] A field looked up by value has a blind index (keyed HMAC); no plaintext copy, no
      unkeyed hash (an unkeyed hash of a phone number is the phone number).
- [ ] Files - audio, images, documents - are encrypted before they reach storage.
- [ ] Nothing that names a person sits in a table, column, or index name, a JSON blob, or a
      file path.
- [ ] Deleting the person's data key makes every new piece of their data unreadable.

## 2. Nothing leaks around the database

- [ ] No log line, at any level, contains identifying or clinical data. Check new logger
      calls, f-strings of model instances, `repr()`, and exceptions that echo input.
- [ ] Error responses do not echo input or reveal internals (SQL, paths, stack traces).
- [ ] Metrics, analytics, and error reports carry opaque IDs only.
- [ ] Notifications and push messages show nothing sensitive on a lock screen by default.
- [ ] Test fixtures contain only invented people. No real names, phones, emails, or IDs.

## 3. Consent and access

- [ ] Recording, sharing a record, referring, and sending text to an LLM each check their own
      consent, by version, and stop when it is withdrawn.
- [ ] Every endpoint checks that this user may see this person's data - not only that they are
      logged in. Therapists see their own clients; one client never sees another.
- [ ] Reads of clinical data write an access-log entry: who, whose, when, why. The log holds
      IDs, not content.
- [ ] Employer, advertiser, and service-provider views are aggregate, and an aggregate over a
      small group (fewer than 5 people) is suppressed.
- [ ] A child's data checks the guardian's consent too.

## 4. AI

- [ ] An LLM prompt carries no identifying fields, and clinical text only with consent for it.
- [ ] AI output is stored as a draft until a professional confirms it.
- [ ] A user-facing AI never claims to be a clinician or diagnoses, and the crisis protocol
      covers it before it ships.

## 5. Secrets and dependencies

- [ ] No key, token, or secret in code, tests, fixtures, `.env.example`, or workflow YAML.
- [ ] The master key and blind-index key are read from the environment, and startup fails if
      either is missing.
- [ ] A new dependency has an ADR and passes `make sec`.
