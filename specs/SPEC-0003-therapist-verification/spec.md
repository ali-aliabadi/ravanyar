---
id: SPEC-0003
title: Therapist signup, credential review and profile activation
status: approved   # draft | approved | implemented | superseded
goal: 1         # which goal in docs/goals.md this serves
data: identifying      # none | identifying | clinical - see AGENTS.md §1.4-§1.5
---

## Problem

A therapist can sign up (SPEC-0001) but nothing checks that they are one. Goal 1 says
credentials are reviewed before a therapist can practise, and clients only ever find
verified therapists.

## Outcome

A therapist fills in a public profile (name, title, specialties, bio, fee), uploads their
licence and other documents, and sends them for review. An admin reads the documents,
compares them with the profile, and approves or rejects with a fixed reason. Only an approved
profile can be found by clients (SPEC-0004). Changing what clients read on an approved profile
sends it back for review.

## Scope

**In:** therapist profile and credential endpoints; credential files encrypted under the
therapist's data key; admin review queue, document download and decision; `grant_admin`
command; admin sign-in for staging test numbers only; `seed_staging` with invented approved
therapists, run after migrations and doing nothing unless `RAVANYAR_PRELAUNCH=1`; the web
screens for both roles.

**Out:** identity verification against a national registry; automatic licence checks with
the psychology council; notifying the therapist by SMS of the decision; client search (SPEC-0004).

## Acceptance criteria

- [ ] Given a therapist, when they open their profile, then it starts as a draft.
- [ ] Given a client, when they call a therapist or admin route, then 403.
- [ ] Given an upload, then the stored bytes are encrypted and the type comes from the file's
  content; anything but PDF, JPEG or PNG up to 5 MB is refused.
- [ ] Given a profile without name, title, fee or a licence, when submitted, then 422; once
  submitted nothing changes until an admin decides.
- [ ] Given a submitted profile, when an admin reads a document, then it is served as a
  download and an allowed `credentials` access-log row is written; another therapist gets
  403 and a denied row.
- [ ] Given an approval, then the profile is active; editing name, title, bio or specialties
  sends it back to review, editing the fee does not.
- [ ] Given a rejection with a reason, the therapist sees the reason, fixes and resubmits.
- [ ] Given a deleted therapist account, the published text is blanked.
- [ ] Given `role: admin` at sign-in, it is refused unless the number is a staging test number.
- [ ] `seed_staging` does nothing unless pre-launch, and is idempotent.

## Data

- **Stored:** the therapist's published profile (name, title, specialties, bio, fee) as
  plaintext public data they write to be found; credential files (licence, degree, national
  ID card), identifying; review state, reviewer and a fixed reject reason.
- **Encrypted:** credential files under the therapist's data key, the row location as
  associated data. Uploads never touch disk unencrypted (memory-only upload handler). The
  published profile is not encrypted: it is shown to every client once approved, and is
  blanked when the account is deleted.
- **Consent:** the therapist's terms and privacy consent (SPEC-0001) covers review of what they
  submit. No new consent.
- **Retention:** until the account is deleted; deletion shreds the data key (files become
  noise) and blanks the published text.
- **Access:** the therapist and admins read credential files, each read access-logged under
  `credentials`. The profile is readable by the therapist and admins, and by clients once
  approved (SPEC-0004).
- **Sent outside:** nothing.

## Open questions

- Which admin accounts exist at launch: `grant_admin` on the server is the only route today.
- Whether a licence number should be checked against the psychology council's public list.
