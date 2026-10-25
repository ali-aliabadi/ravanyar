---
id: SPEC-0001
---

Each task is one commit-sized unit. Every acceptance criterion maps to at least one named
test, so a reviewer can check coverage by reading this file.

| # | Task | Test that proves it |
|---|------|---------------------|
| 1 | Add `cryptography`; `crypto.py` with key loading, wrap/unwrap, encrypt/decrypt, blind index | `src/core/tests/test_crypto_unit.py::test_round_trip`, `::test_aad_mismatch_fails`, `::test_other_persons_key_fails`, `::test_blind_index_is_keyed` |
| 2 | `normalise_phone` | `src/core/tests/test_crypto_unit.py::test_phone_forms_normalise` (Latin, Persian, Arabic-Indic digits), `::test_non_iranian_or_landline_rejected` |
| 3 | Models, `AUTH_USER_MODEL`, first migration with access-log trigger | `src/core/tests/test_access_integration.py::test_access_log_rejects_update_and_delete` |
| 4 | `access.py`: `authorize`, `Grant`, `read_phone` | `src/core/tests/test_access_integration.py::test_self_read_allowed_and_logged`, `::test_other_subject_denied_and_logged` |
| 5 | `sms.py` Kavenegar call | `src/core/tests/test_sms_unit.py::test_sends_lookup_and_logs_status_only` |
| 6 | `services.py` sign-in: request and verify code, rate limits, attempts, expiry | `src/core/tests/test_signin_integration.py::test_request_same_response_with_or_without_account`, `::test_rate_limited`, `::test_wrong_code_five_times_kills_code`, `::test_expired_or_used_code_refused`, `::test_first_signin_creates_account_and_consents`, `::test_admin_role_rejected` |
| 7 | `auth.py` bearer, default auth on `NinjaAPI`, logout, expiry | `src/core/tests/test_default_deny_unit.py::test_every_route_requires_auth`, `src/core/tests/test_signin_integration.py::test_no_or_bad_token_401`, `::test_logout_revokes`, `::test_expired_session_401` |
| 8 | Consent ledger services and `/me/consents` endpoints | `src/core/tests/test_consent_integration.py::test_list_consents`, `::test_withdrawn_or_outdated_consent_blocks`, `::test_regrant_adds_row` |
| 9 | `GET /me`, `DELETE /me` (crypto-shred) | `src/core/tests/test_access_integration.py::test_self_read_allowed_and_logged`, `src/core/tests/test_deletion_integration.py::test_delete_shreds`, `::test_resignup_creates_new_account` |
| 10 | Leak test over a seeded database | `src/core/tests/test_leak_integration.py::test_no_phone_in_any_column` |
| 11 | Key validation at startup; `prod.py` refuses draft consent versions | `src/core/tests/test_settings_unit.py::test_bad_or_missing_key_refuses_start`, `src/core/tests/test_settings_unit.py::test_prod_refuses_draft_consent` |
| 12 | Flip `status: approved` to `implemented` | `make spec` |
