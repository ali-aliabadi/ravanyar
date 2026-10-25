---
id: SPEC-0001
---

## Approach

Everything stays in the existing `core` app. New modules, each well under 300 lines:

- `core/crypto.py`: pure functions with no Django ORM. It loads and validates the master and
  blind-index keys from settings (32 bytes, base64), and provides `new_data_key`, `wrap`,
  `unwrap`, `encrypt(key, aad, plaintext)` and `decrypt(key, aad, blob)`, using AES-256-GCM
  from `cryptography` with a random 96-bit nonce prefixed to the ciphertext. It also provides
  `blind_index(value)` (HMAC-SHA256, stdlib) and `normalise_phone(raw)`. Settings call the
  key loader, so a bad key stops startup.
- `core/models.py`: persistence only. `Account` (`AbstractBaseUser` with a UUID pk, `role`,
  `phone_ct`, `phone_index` unique and nullable, `wrapped_key`, `created_at`, `deleted_at`,
  and an unusable password), `SignInCode`, `AuthSession`, `Consent`, `AccessLog`.
  `AUTH_USER_MODEL = "core.Account"` is set before the first migration, because it cannot
  sensibly change afterwards. The first migration also creates a trigger that raises on
  `UPDATE` or `DELETE` of `core_accesslog`.
- `core/access.py`: `authorize(actor, subject, purpose) -> Grant`. It writes an `AccessLog`
  row on every call, and raises `Denied` unless a rule allows. The one rule here is
  `actor == subject`. `read_phone(grant, account)` is the only way to decrypt a phone. It
  checks that the grant's subject owns the data key, so a missing `authorize` call cannot be
  skipped quietly. Later specs add their rules here, and nowhere else.
- `core/sms.py`: one function, `send_code(phone, code)`. It makes a single `urllib.request`
  call to Kavenegar's `verify/lookup` endpoint, reads `KAVENEGAR_API_KEY` and
  `KAVENEGAR_TEMPLATE` from the environment, has a 5-second timeout, and logs only the HTTP
  status. Tests patch it.
- `core/services.py`: `request_code`, `verify_code`, `logout`, `delete_account`,
  `grant_consent`, `withdraw_consent`, `has_current_consent`. The rate limits are count
  queries on `SignInCode` by `phone_index`, with no cache needed. `request_code` also deletes
  codes older than 24 hours.
- `core/auth.py`: a ninja `HttpBearer` that hashes the presented token, loads an
  unexpired, unrevoked session on an active account, and returns the account. A subclass
  also requires current `terms` and `privacy` consent. The subclass is the default on the
  `NinjaAPI`. Consent, logout and delete routes use the base class; `health`, `ready`,
  `request_code` and `verify_code` set `auth=None`.
- `core/api.py` gains the routers for `/auth`, `/me` and `/me/consents`. They stay thin and
  call one service each. If it passes 300 lines it splits into `api_auth.py`.

`cryptography` is added to `pyproject.toml` under ADR 0004's pre-authorisation. Test
settings generate both keys with `os.urandom` at import, so no key-like literal enters the
repo for gitleaks to flag.

Consent versions: `CURRENT_VERSIONS = {"terms": "terms-draft-0", "privacy": "privacy-draft-0"}`
in `services.py`. Publishing a new version means changing that constant, and every account
must accept it again.

## Alternatives rejected

- **Email and password.** Rejected by ali on 2026-10-25 in favour of phone and SMS code: it
  matches how Iranian users sign in, and there is no password column to defend.
- **Django's built-in `User`.** It has plaintext `username`, `email`, `first_name` and
  `last_name`, which breaks ADR 0004 from the first row.
- **Django sessions with cookies and CSRF.** These suit a browser only, and the client app
  (web or mobile) is undecided. A bearer token works for both. If the client turns out to be
  a web app, cookies can be reconsidered then.
- **A separate `DataKey` table.** A nullable column on `Account` shreds the same way with one
  table fewer.
- **Role checks (`is_therapist`) in views.** They answer "may a therapist see clients"
  instead of "may this therapist see this client". One `authorize` with a grant-gated
  decrypt is the only place that question is answered.
- **App-only append-only log.** An app bug or a careless migration could rewrite history. A
  trigger costs about ten lines of SQL. It does not stop a database superuser, and is not
  meant to.
- **A `kavenegar` pip package.** It wraps one HTTPS GET. The stdlib does that, so there is no
  dependency and no ADR.

## Risks

- **The Kavenegar API key sits in the request URL path** (their API design). Outbound proxies
  or error reports that capture URLs would leak it. Mitigation: errors log only the status,
  never the URL.
- **Sequential IDs leak.** All primary keys exposed through the API are UUIDs. Internal
  tables keep `BigAutoField`, which reveals row counts in a dump, an accepted residual risk
  under ADR 0004.
- **Per-request unwrap cost.** One AES-GCM unwrap per decrypted read is microseconds. Not a
  concern until profiling says otherwise.
- **Placeholder consent versions reaching production.** The early warning: `prod.py` refuses
  to start while any `CURRENT_VERSIONS` value ends in `-draft-0`.
- **Persian digits.** If normalisation misses them, users cannot sign in from a Persian
  keyboard. Covered by the normalisation unit tests.
