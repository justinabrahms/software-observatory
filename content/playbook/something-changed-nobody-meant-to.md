---
order: 40
kind: symptom
title: "Something changed that nobody meant to change"
noticed: >-
  The change was supposed to add one field. A consumer broke, or a page
  rendered differently, and nobody in review noticed the second thing
  move.
doubt: unintended-change
sensor: api-compatibility
next: every-service-passes-alone
---

## Point this at it

Which sensor depends on what moved. For a published interface, an
OpenAPI spec, a gRPC service, a JVM library, use
[API compatibility](api-compatibility.html): run openapi-diff on the
old and new spec in CI, or revapi or MiMa on the old and new jar, and
fail the build on any line classified BREAKING. That takes seconds, needs
no deployment, and has to know nothing about who is calling.

For rendered output, HTML, a JSON body, a generated report, use
[snapshot tests](snapshot-tests.html): record one snapshot of the output
the last surprise came from, with Jest or Vitest, commit it, and read the
diff every time it fails before touching the update flag.

## Reading it

- Red from compatibility: a removed endpoint or a changed type, named.
  It tells you what you did, and cannot tell you what it costs; go find
  out who is on the other end before deciding. Red from a snapshot: a
  diff. Decide intended or accidental, and if forty files moved, say the
  shared cause in one sentence or approve nothing.
- Green: the interface shape held, or the output matched the recording.
- It does not prove the meaning held. A flipped default or a field that
  now means something else passes the compatibility check, and a surface
  no spec describes produces no verdict at all. A snapshot cannot tell
  you the original recording was right.

## If the doubt survives

If the shape held and the output matched and something downstream still
broke, the pieces changed how they behave together rather than what they
expose. That is emergent failure, and the next play covers it.
