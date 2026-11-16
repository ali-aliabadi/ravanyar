---
id: SPEC-0003
---

| # | Task | Test that proves it |
|---|------|---------------------|
| 1 | Profile starts as draft | `backend/src/core/tests/test_verification_integration.py::test_profile_starts_as_draft` |
| 2 | Role checks | `::test_client_cannot_use_therapist_or_admin_routes` |
| 3 | Encrypted upload, sniffed type | `::test_upload_is_encrypted_and_type_comes_from_content` |
| 4 | Submit rules, frozen while under review | `::test_submit_needs_profile_and_licence` |
| 5 | Admin reads (logged) and approves; edits re-review | `::test_admin_reviews_reads_credential_and_approves` |
| 6 | Reject and resubmit | `::test_reject_with_reason_lets_therapist_fix_and_resubmit` |
| 7 | Other therapist denied and logged | `::test_other_therapist_cannot_read_credential` |
| 8 | Deletion blanks the profile | `::test_deleting_therapist_blanks_published_profile` |
| 9 | Admin sign-in only for test numbers | `::test_admin_sign_in_only_for_staging_test_numbers`, `test_signin_integration.py::test_admin_role_rejected` |
| 10 | `grant_admin`, `seed_staging` | `::test_grant_admin_needs_an_existing_account`, `::test_seed_only_on_prelaunch_and_idempotent` |
