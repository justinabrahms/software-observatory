---
order: 20
kind: composition
title: "A minimal stack for a library with downstream users"
shape: >-
  A package other teams import. It has no production of its own; a release
  that breaks a caller is the failure mode.
stack:
  - sensor: api-compatibility
    closes: [unintended-change]
    why: Classifies the surface diff in seconds and needs no consumer list.
  - sensor: property-based-testing
    closes: [wrong-logic]
    why: Callers send inputs you never thought of; so does the generator.
  - sensor: mutation-testing
    closes: [unasserted-execution]
    why: A library is small enough to mutate whole on every release.
  - sensor: type-checker
    closes: [not-internally-consistent]
    why: Published types are part of the contract; check them before callers do.
  - sensor: documentation-drift
    closes: [unexplained]
    why: Doctests; the README example is the first code every user runs.
  - sensor: escaped-defect-rate
    reveals: [wrong-specification, missing-behavior, late-effects]
    why: Downstream bug reports are the only production signal a library gets.
left_open:
  - doubt: untested-conditions
    reason: >-
      Both closers split live traffic between two versions, and a library
      has no traffic. Its users' production is where the untried inputs
      live, and their canary is what sees them.
  - doubt: dependency-failure
    reason: >-
      A library does not own the database or the network that fails. The
      application that wires it to them does, and fault injection belongs
      there.
  - doubt: unjudged-observation
    reason: >-
      No production of its own, so no observations to judge. The
      invariants that would judge them are each user's, written in their
      domain's terms.
  - doubt: does-not-run-where-deployed
    reason: >-
      Every user deploys it somewhere different, and only their smoke test
      runs there. Yours can cover the install and nothing past it.
---

Every row but one runs before a release, because a release is the only
event a library has. The exception is the [escaped defect
rate](escaped-defect-rate.html), which is your users' production read back
through their bug reports. It lags by months, and it is still the only
sensor here that can tell you the property you tested for was the wrong
one.
