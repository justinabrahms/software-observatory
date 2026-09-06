---
order: 80
kind: symptom
title: "The agent wrote it, the agent reviewed it, both agreed"
noticed: >-
  A coding agent wrote the change. A second pass, by the same model or a
  differently prompted one, approved it. The bug both of them missed was
  in an assumption both of them share.
doubt: correlated-blind-spot
sensor: independent-review
---

## Point this at it

[Independent review](independent-review.html) by one person who did not
write the change and did not prompt the agent that wrote it. Choose the
reviewer for distance from the author rather than for seniority. Ask for
one thing in writing: what does this change do, and what does it break
elsewhere? A review that quotes the caller, the schema, or the spec is
doing the work; one that reads only the diff is checking the change
against itself.

Keep the change small enough that a human can read all of it. A second
model, session, or prompt reviewing the same code is a different sensor
and does not close this doubt, because the thing it checks against can
share the original's blind spot.

## Reading it

- Red: specific objections that name functions, inputs, and failure
  modes. Reproduce blocking findings before arguing. When author and
  reviewer disagree about what the code does, at least one of them holds
  a wrong model, and that disagreement is what you paid for.
- Green: a reviewer who opened the callers found nothing to object to.
  Judge it by the specificity of what they wrote; "looks good" is not a
  reading.
- It does not prove anything if the approval came in ninety seconds on a
  forty-file diff. Time from request to approval, per reviewer, tells you
  whether a review happened.

## If the doubt survives

If a careful stranger reads the change against its callers and agrees,
and it is still wrong, the shared belief is probably about what the
system should do. That is wrong specification, and the same reviewer can
reach it only by checking the change against the requirement rather than
against the author's description of it.
