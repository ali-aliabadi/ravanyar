---
id: SPEC-0004
---

| # | Task | Test that proves it |
|---|------|---------------------|
| 1 | Search returns only approved, active profiles | `backend/src/core/tests/test_search_integration.py::test_only_approved_profiles_are_found` |
| 2 | Text match with Persian normalisation | `backend/src/core/tests/test_search_integration.py::test_search_matches_letter_variants_and_half_spaces` |
| 3 | Search filters by specialty, and by text too | `backend/src/core/tests/test_search_integration.py::test_search_filters_by_specialty` |
| 4 | Bad specialty code is 422, not echoed | `backend/src/core/tests/test_search_integration.py::test_unknown_specialty_is_refused` |
| 5 | Back in review or deleted means not found | `backend/src/core/tests/test_search_integration.py::test_profile_leaves_search_when_not_approved` |
| 6 | Public profile 404 unless approved | `backend/src/core/tests/test_search_integration.py::test_public_profile_hides_unapproved` |
| 7 | Search text and specialty never logged | `backend/src/core/tests/test_search_integration.py::test_search_text_is_not_logged` |
| 8 | Unknown or more than five specialties refused | `backend/src/core/tests/test_specialty_integration.py::test_profile_refuses_unknown_or_too_many` |
| 9 | Changing specialties sends an approved profile to review | `backend/src/core/tests/test_specialty_integration.py::test_specialty_change_needs_review` |
| 10 | Migration maps old text to codes | `backend/src/core/tests/test_specialty_unit.py::test_old_text_maps_to_codes` |
| 11 | Deletion blanks profile and specialties | `backend/src/core/tests/test_verification_integration.py::test_deleting_therapist_blanks_published_profile` |
| 12 | Approved therapist adds slots; window and overlap refused | `backend/src/core/tests/test_booking_integration.py::test_therapist_adds_slots_within_rules` |
| 13 | Unapproved therapist cannot add slots | `backend/src/core/tests/test_booking_integration.py::test_unapproved_therapist_cannot_add_slots` |
| 14 | Client sees open, bookable slots only | `backend/src/core/tests/test_booking_integration.py::test_client_sees_open_slots_only` |
| 15 | A slot cannot be booked twice | `backend/src/core/tests/test_booking_integration.py::test_same_slot_cannot_be_booked_twice` |
| 16 | Client cancel reopens the slot; not after start | `backend/src/core/tests/test_booking_integration.py::test_client_cancel_reopens_slot` |
| 17 | Therapist cancel withdraws the slot | `backend/src/core/tests/test_booking_integration.py::test_therapist_cancel_withdraws_slot` |
| 18 | Roles and ownership | `backend/src/core/tests/test_booking_integration.py::test_roles_and_ownership` |
| 19 | Deletion cancels future bookings | `backend/src/core/tests/test_booking_integration.py::test_deletion_cancels_future_bookings` |
| 20 | Therapist never sees client id or phone | `backend/src/core/tests/test_booking_integration.py::test_therapist_never_sees_client` |
| 21 | Client moves a booking; a taken slot changes nothing | `backend/src/core/tests/test_booking_extras_integration.py::test_client_moves_booking` |
| 22 | Weekly slots skip what does not fit | `backend/src/core/tests/test_booking_extras_integration.py::test_weekly_slots_skip_what_does_not_fit` |
| 23 | Therapist sees a booked client's first name, logged; ciphertext at rest | `backend/src/core/tests/test_booking_extras_integration.py::test_therapist_sees_first_name_of_booked_client_only` |
| 24 | Deletion drops the first name | `backend/src/core/tests/test_booking_extras_integration.py::test_deleting_client_drops_name` |
| 25 | Reminders: SMS for real numbers, log for test numbers, once, logged | `backend/src/core/tests/test_booking_extras_integration.py::test_reminders_like_sign_in_codes` |
| 26 | Reminder SMS carries a weekday and a time only | `backend/src/core/tests/test_sms_unit.py::test_reminder_sends_weekday_and_time_only` |
| 27 | No token is 401 | `backend/src/core/tests/test_default_deny_unit.py::test_no_token_is_401_everywhere_but_public` |
| 28 | Web: search, booking, move, first name, week picker with repeat | manual on the local stack; the web client has no test runner |
