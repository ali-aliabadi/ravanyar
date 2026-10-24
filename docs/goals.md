# Goals

Why Ravanyar exists, in priority order. Ravanyar is a mental-health platform: clients find a
verified therapist, are cared for across sessions, and get AI help that supports a
professional and never replaces one.

This file names what the work is for, not what is built next. The order is the order of
priority: Goal 1 is the core product, and a later goal does not start crowding it out. Every
spec states which goal it serves; a spec that serves none of these is either a goal we have
not written down yet, or work we should not do.

Security, consent, and the crisis protocol are not goals to reach later. They are rules every
goal obeys from the first line of code - see [AGENTS.md](../AGENTS.md) §1.

## Goal 1 - Safe, continuous care between a client and their therapist

A client finds a therapist whose identity and credentials are verified, books and pays for a
session, meets online, and their care continues across sessions instead of restarting each
time.

- **Onboarding and verification** - identity checked to the level the role needs;
  therapists' credentials reviewed before they can practise; each consent recorded with the
  document version and time it was given.
- **Booking, payment, online sessions** - no slot can be booked twice; payment state comes
  from the gateway's confirmation, never from the client.
- **The mental-health record** - one longitudinal record per client. A professional sees only
  what they need and are permitted to see; every access is logged; sharing with another
  professional needs the client's consent.
- **Session assistant** - transcribes a session only with the client's consent and drafts
  notes that the therapist edits and confirms. A draft is never a clinical fact.

## Goal 2 - AI help that supports, never replaces, a professional

Help between sessions: an assistant that answers general mental-health questions from
traceable sources, content picked for the person, a private journal, and a planner for the
exercises a therapist sets.

It never presents itself as a clinician and never diagnoses. Signs of crisis trigger the
safety protocol and a route to a human. Private entries stay private unless the person shares
them, and personalisation can be switched off.

## Goal 3 - A trustworthy professional network

Professionals referring clients to each other, including complex cases that need several
specialists; feedback on professionals that is fair to both sides; standardised
psychological assessments; and an academic space for researchers and psychology students.
Referral shares the minimum, with the client's consent. Case studies are fictional or
properly anonymised.

## Goal 4 - A sustainable business

A marketplace for books, courses and workshops; secure paid learning packs; Ravanyar's own
content; and introductions to legal, financial and family services. Advertising is labelled
as advertising, and no advertiser or service provider sees anything from a client's record or
conversations.

## Goal 5 - New audiences

Organisations, children and the wider culture: workplace programmes whose reports are
aggregate and cannot identify an individual even in small teams; games and training for
children and the people who care for them; psychology through film and art.

---

## Not a software goal

Institutional work - knowledge-based company status, tax incentives, university partnerships,
an affiliated charity - runs in parallel as a business track. No spec serves it.

## How a spec uses this

Each spec's front matter carries `goal:` naming the goal it serves. When scope grows in
review, the question is whether the new part serves the same goal - and if it serves a
different one, it is a different spec.

Goals change by amending this file in its own PR, with the reasoning in the PR body. They are
not edited in passing as part of a feature.
