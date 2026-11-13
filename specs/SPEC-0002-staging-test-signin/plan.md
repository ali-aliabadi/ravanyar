---
id: SPEC-0002
---

## Approach

`config/settings/prod.py` parses the two variables and refuses to start unless
`RAVANYAR_PRELAUNCH=1` and the code is 6 digits. `base.py` defaults them to empty, so dev and
test never run in test mode unless a test overrides it. `core.services.request_code` stores
the hash of the fixed code for a listed number and returns before calling Kavenegar;
everything after that (expiry, 5 attempts, consent, session) is the unchanged SPEC-0001 path.

## Alternatives rejected

- A fake SMS backend that shows the code: real numbers would still be used on staging.
- A "production" marker that blocks test mode: forgetting to set it would leave the bypass
  open. Requiring the existing pre-launch flag fails closed instead.

## Risks

The launch server keeps `RAVANYAR_PRELAUNCH=1` by mistake and copies the staging `.env`. The
launch checklist already says generate fresh secrets and never copy this `.env`; the
`/api/health` `test_mode` field makes it visible from outside.
