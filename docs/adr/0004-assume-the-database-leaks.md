# 4. Assume the database leaks

**Status:** accepted
**Date:** 2026-10-25

## Context

Ravanyar will hold session transcripts, mental-health records, journals and assessment
results, and the fact that someone is a client here is itself sensitive. Databases leak:
through a stolen backup, a misconfigured replica, an SQL injection, or an insider's export.
The design question is not whether a dump gets out, but what it reveals when it does.

Disk encryption and Postgres-level encryption do not answer it. They protect a stolen disk,
but everything that can query the database - the app, a replica, `pg_dump`, an injection -
reads plaintext straight through them.

## Decision

**A full dump of the database and its backups, published, must not reveal who anyone is or
anything clinical about them.**

What a table may hold in plaintext: opaque IDs, foreign keys, timestamps, status enums,
amounts, and data that is public anyway (a therapist's public profile, published content).
Everything else is one of two classes and is encrypted by the application before it is
written:

- **Identifying** - name, phone, email, national ID, address, date of birth, IP address,
  payment references, and anything else that points at a real person.
- **Clinical** - everything AGENTS.md §1.4 lists: session audio and transcripts, notes,
  records, journals, assessment results, assistant conversations.

How:

1. **Envelope encryption, one key per person.** Each person gets a random 256-bit data key.
   Their identifying and clinical fields, and their files (session audio, voice journals), are
   encrypted with it using AES-256-GCM. The ciphertext is bound to its location (table, column,
   row id) as associated data, so it cannot be copied into another row and decrypted there.
2. **Data keys are stored wrapped.** The data key is stored in the database only in encrypted
   form, under a master key that lives outside the database: an environment secret now, a
   KMS once one exists. The master key is never in the database, its backups, the repo, or a
   log.
3. **Lookups use a blind index.** Fields we must find by value - phone or email at login, a
   uniqueness check - also store an HMAC-SHA256 of the normalised value, under a second key
   that is also outside the database. Equality lookups work; nothing else does.
4. **Deletion is crypto-shredding.** Deleting a person's data key makes all of their data
   unreadable everywhere, including in backups we cannot rewrite. That is how retention limits,
   account deletion and withdrawn consent reach the backups.
5. **Only opaque IDs leave the app.** Logs, metrics, error reports, analytics and LLM prompts
   carry opaque IDs. Clinical text reaches an LLM only under §1.4's consent rule, never with
   identifying fields attached.

`cryptography` (pyca) provides AES-GCM, which the standard library does not. This ADR is the
written reason to add it, together with the first spec that stores encrypted data. HMAC comes
from the standard library.

## Consequences

- **What a leak still reveals:** row counts, timestamps, ciphertext sizes, and links between
  opaque IDs - for example, that some unnamed client saw therapist T every Monday. Nobody can
  be named without the keys. We accept this residual risk.
- **What this does not protect against:** an attacker holding the running app server, which
  has the keys. Least privilege, an access audit log, and a KMS with its own audit trail cover
  that case; they are separate decisions.
- **No SQL search, sort, or range filters on encrypted fields.** Searching by name happens in
  the app, over a list that is already scoped (a therapist's own clients). Reports run on the
  plaintext operational fields.
- **Losing the master key loses all the data.** Before production, the master key and the
  blind-index key need a written backup and rotation procedure. Rotating the master key
  rewraps the data keys; it does not re-encrypt the data.
- **Low-entropy fields need their key.** A phone number has few possible values, so its blind
  index can be brute-forced by someone who also holds the blind-index key. That key gets the
  same protection as the master key.
