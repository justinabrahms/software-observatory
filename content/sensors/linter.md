---
id: SO-001c
title: Linter
family: structural
family_num: "01"
oracle: medium
independence: high
scope: module
latency: milliseconds
actionability: guiding
type: predictive
stack_level: static-analysis
categories:
  - Structural
  - Guiding Sensors
see_also:
  - SO-001
  - SO-001b
  - SO-001d
last_reviewed: 2026-08-23
---

Catches structural inconsistencies that are syntactically valid but
semantically suspect. Lower oracle strength than a [type
checker](type-checker.html), but faster feedback on style and common traps.

A linter sits between [compilation](compiler.html) and [type
checking](type-checker.html) — it catches things the compiler won't (unused
variables, unreachable code, style violations) but with less authority. A
linter can be wrong; a compiler cannot.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — suggestions, not facts |
| Independence | High — external to the code |
| Scope | Module-level |
| Feedback latency | Milliseconds |
| Actionability | Guiding — shows the exact line and rule |
| Type | Predictive |

## What it cannot detect

A linter cannot detect [behavioral correctness](catalog.html#behavioral) —
it operates on syntax and patterns, not execution. It also produces false
positives, which erodes its authority over time.

## Tooling

- ESLint
- ruff
- golangci-lint
- Semgrep

## References

- Gang of Eight: A Defect Taxonomy for Infrastructure as Code Scripts (2020, tier II) — https://akondrahman.github.io/files/papers/icse20_acid.pdf
- The Seven Sins: Security Smells in Infrastructure as Code Scripts (2019, tier II) — https://akondrahman.github.io/files/papers/icse19_slic.pdf

- https://en.wikipedia.org/wiki/Lint_(software)