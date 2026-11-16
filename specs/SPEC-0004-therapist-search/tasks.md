---
id: SPEC-0004
---

| # | Task | Test that proves it |
|---|------|---------------------|
| 1 | Search returns only approved, active profiles | `backend/src/core/tests/test_search_integration.py::test_only_approved_profiles_are_found` |
| 2 | Text match with Persian normalisation | `backend/src/core/tests/test_search_integration.py::test_search_matches_letter_variants_and_half_spaces` |
| 3 | Back in review or deleted means not found | `backend/src/core/tests/test_search_integration.py::test_profile_leaves_search_when_not_approved` |
| 4 | Public profile 404 unless approved | `backend/src/core/tests/test_search_integration.py::test_public_profile_hides_unapproved` |
| 5 | Search text never logged | `backend/src/core/tests/test_search_integration.py::test_search_text_is_not_logged` |
| 6 | No token is 401 | `backend/src/core/tests/test_default_deny_unit.py::test_no_token_is_401_everywhere_but_public` |
| 7 | Client screen: search, results, profile | manual on staging; the web client has no test runner |
