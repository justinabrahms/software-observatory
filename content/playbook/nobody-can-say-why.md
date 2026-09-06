---
order: 100
kind: symptom
title: "Nobody can say why the code is like this"
noticed: >-
  A line looks wrong. You ask around, and the person who wrote it has
  left. The commit message says "fix". Nobody can tell you whether it is
  safe to remove.
doubt: unexplained
sensor: decision-provenance
---

## Point this at it

[Decision provenance](decision-provenance.html), as one timed
reconstruction. Take the line and work backwards: git blame for the
commit, git log -S on the odd term, git show for the diff and any linked
ticket, then a grep of the ADR directory. Fill in
five answers: what it does, when it changed, why, what was rejected
instead, and whether the reason still holds. The time this takes is the
reading; every future change to the line pays it again.

Write whatever you find at the site the same day, as an ADR or a comment
naming one. If docs exist and describe a system that is not the one in
front of you, that is a different sensor:
[documentation drift](documentation-drift.html) compares what the docs
claim against what the code does.

## Reading it

- Red: the why survives as a commit subject, or not at all. Ask the
  author if reachable and record the answer. If nobody knows, mark the
  gap at the site: reason lost, do not change without re-deriving the
  invariant.
- Green: an ADR the code links to, with rejected alternatives, whose
  reason still applies. Check the age; why the line was added and why it
  is still there are separate questions.
- It does not prove anything about decisions that were never recorded.
  A reason given verbally, in a deleted branch, or in a private message
  is invisible to it.

## If the doubt survives

Knowing why the line is there does not tell you it is right. If the
recorded reason was a constraint that no longer holds, the code is wrong
for a reason everyone can now name, and that reason specifies the test
that shows it. That is wrong logic, or wrong specification if the
original reasoning was itself mistaken.
