---
id: SPEC-0003
---

## Approach

`core/models/` becomes a package (one module per area) so later specs do not grow one file.
`TherapistProfile` (one per therapist account) and `Credential` live in
`core/models/practice.py`. `core/verification.py` holds the services; `core/api_verification.py`
the routes. `core.access` gains `seal`/`unseal` for any per-person ciphertext and one rule:
an admin may read a therapist's credentials. Admins come from `grant_admin`, or, on staging,
from signing in as admin with a test number. `core/seed.py` holds invented demo data, run by
`seed_staging` after `migrate` in the compose stack; it returns at once unless pre-launch.

## Alternatives rejected

- Encrypting the published profile: it is shown to every client, and search needs to read it;
  the leak test allows public data.
- Files on disk or object storage: one more thing to encrypt, back up and delete. Encrypted
  blobs in Postgres are fine at this size.
- An admin flag set by environment variable: a second way to become admin that lingers.

## Risks

nginx's default 1 MB body limit cuts uploads short: the snippet now sets 6 MB on `/api/`.
