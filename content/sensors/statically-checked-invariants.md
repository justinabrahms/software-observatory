---
id: SO-013
title: Statically Checked Invariants
family: invariants
family_num: "04"
oracle: high
independence: high
scope: module
latency: milliseconds
actionability: blocking
type: predictive
stack_level: static-analysis
categories:
  - Invariants
  - Formal Methods
see_also:
  - SO-004
  - SO-012
  - SO-001d
last_reviewed: 2026-08-23
---

Invariants the compiler refuses to let you violate: Dafny `invariant`
clauses, Frama-C annotations, JML specs, type-level witnesses like
`NonEmptyList`. Where [database invariants](database-invariants.html) are
checked by a live system against live data, these are proved once, at build
time, for all possible executions.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — a discharged proof obligation is definitive for its claim |
| Independence | High — the prover is outside the code |
| Scope | Module |
| Feedback latency | Milliseconds to minutes |
| Actionability | Blocking — the build fails |
| Type | Predictive |

## What it cannot detect

Invariants that were never written down, and invariants whose statement is
wrong. The gap between "the invariant holds" and "the invariant is the one
the business needs" is exactly what [business invariants](business-invariants.html)
measure from the other direction.

## Tooling

- Dafny
- Frama-C
- JML
- Liquid Haskell

## References

- How Amazon Web Services Uses Formal Methods (2015, tier III) — https://cacm.acm.org/research/how-amazon-web-services-uses-formal-methods/

- Leino, 'Dafny' (2010)
- Liquid Haskell: https://ucsd-progsys.github.io/liquidhaskell/