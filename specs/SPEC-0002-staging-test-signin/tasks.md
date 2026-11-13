---
id: SPEC-0002
---

| # | Task | Test that proves it |
|---|------|---------------------|
| 1 | Settings refuse test numbers without pre-launch | `backend/src/core/tests/test_settings_unit.py::test_test_phones_refused_without_prelaunch` |
| 2 | Settings refuse a bad code | `backend/src/core/tests/test_settings_unit.py::test_test_phones_need_a_six_digit_code` |
| 3 | Fixed code, no SMS, logged | `backend/src/core/tests/test_staging_signin_integration.py::test_test_phone_uses_fixed_code_without_sms` |
| 4 | Other numbers unchanged | `backend/src/core/tests/test_staging_signin_integration.py::test_other_numbers_still_get_a_real_sms` |
| 5 | Off by default | `backend/src/core/tests/test_staging_signin_integration.py::test_fixed_code_does_nothing_when_test_mode_is_off` |
