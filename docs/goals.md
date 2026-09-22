# Goals

Why this project exists, in priority order. Written down before any direction was chosen, so
that later decisions can be checked against it rather than against memory.

**This is not a roadmap and not an MVP.** It names what the work is for. What gets built first
is still undecided, deliberately. Every spec states which goal it serves; a spec that serves
none of these is either a goal we have not written down yet, or work we should not do.

## Goal 1 - A personalised helper, for the student and for the school

Education has changed now that LLMs are in it, and a student working alone gets no help
shaped around them. The helper suggests what to practise next and supports a student through
difficult mental states, not only difficult material.

Personalised along two axes at once:

- **For the student** - their pace, their gaps, their state on the day.
- **For the school** - the curriculum, constraints, and standards the student sits inside.

A helper that serves only one axis is a different product. Both, together, is the goal.

## Goal 2 (side) - Room for different educational paths

For students who want to try a route other than the standard one. The system should not
assume a single correct sequence through a subject, or a single definition of progress.

## Goal 3 (side) - The same quality of content, for everyone

Quality teaching content should not depend on which school a student happens to attend. Where
goals 1 and 2 personalise, this one levels: the same standard of material reaching everyone.

---

## How a spec uses this

Each spec's front matter carries `goal:` naming the goal it serves. When scope grows in
review, the question is whether the new part serves the same goal - and if it serves a
different one, it is a different spec.

Goals change by amending this file in its own PR, with the reasoning in the PR body. They are
not edited in passing as part of a feature.
