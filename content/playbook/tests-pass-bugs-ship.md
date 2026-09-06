---
order: 10
kind: symptom
title: "Tests pass, bugs still ship"
noticed: >-
  CI is green on every merge. Bugs reach production anyway, and when you
  look, there was a test near the bug that never failed.
doubt: unasserted-execution
sensor: mutation-testing
next: bugs-in-inputs-nobody-tried
---

## Point this at it

[Mutation testing](mutation-testing.html), once, on the one module the
last bug came from. Do not run it across the repository and do not set a
threshold yet. Point mutmut, Stryker, PIT, or cargo-mutants at that
module's files and read only the survivor list. Each survivor names a
file, a line, and the expression the tool changed while every test kept
passing.

Then look for the test that sat next to the bug. If negating the
condition it was supposed to check survives, that test runs the line and
asserts nothing about it.

## Reading it

- Red: survivors in the module. Each one is a behavior the suite lets
  change without noticing. Write the assertion the mutant demands, with
  the mutated expression as the spec, and start with survivors in
  validation, billing, and access control.
- Green: every mutant killed, timeouts included. The tests do notice
  when this code changes in the ways the tool's operators can produce.
  No-coverage mutants are a separate reading; they belong to the
  coverage question, since the code never ran under any test.
- It does not prove the tests would catch a wrong implementation the
  operators cannot produce, an input the tests never supply, or a
  feature that was never written.

## If the doubt survives

If the module's mutants all die and it keeps shipping bugs, the tests
are asserting, and asserting the right thing for the inputs they use.
The failing input is one they never used. That is wrong logic showing
up outside the examples, and the next play is written for it.
