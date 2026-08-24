---
id: SO-001c
title: Linter
family: structural
family_num: '01'
oracle: medium
oracle_note: suggestions, not facts
independence: high
independence_note: external to the code
scope: module
latency: milliseconds
actionability: guiding
actionability_note: shows the exact line and rule
type: predictive
stack_level: static-analysis
categories:
- Structural
see_also:
- SO-001
- SO-001b
- SO-001d
last_reviewed: '2026-08-24'
references:
- title: 'Gang of Eight: A Defect Taxonomy for Infrastructure as Code Scripts'
  year: 2020
  tier: II
  url: https://akondrahman.github.io/files/papers/icse20_acid.pdf
  kind: paper
  authors: Akond Rahman, Effat Farhana, Chris Parnin, Laurie Williams
  venue: ICSE 2020
- title: 'The Seven Sins: Security Smells in Infrastructure as Code Scripts'
  year: 2019
  tier: II
  url: https://akondrahman.github.io/files/papers/icse19_slic.pdf
  kind: paper
  authors: Akond Rahman, Chris Parnin, Laurie Williams
  venue: ICSE 2019
- title: ESLint
  kind: tool
  url: https://eslint.org
  description: Pluggable JavaScript/TypeScript linter
- title: ruff
  kind: tool
  url: https://docs.astral.sh/ruff
  description: Fast Python linter and formatter
- title: golangci-lint
  kind: tool
  url: https://golangci-lint.run
  description: Go linter aggregator
- title: Semgrep
  kind: tool
  url: https://semgrep.dev
  description: Multi-language static analysis with custom rules
---

Catches structural inconsistencies that are syntactically valid but
semantically suspect. Lower oracle strength than a [type
checker](type-checker.html), but faster feedback on style and common traps.

A linter sits between [compilation](compiler.html) and [type
checking](type-checker.html) — it catches things the compiler won't (unused
variables, unreachable code, style violations) but with less authority. A
linter can be wrong; a compiler cannot.

## How it gets gamed

Linter authority is a budget, and it can be spent:

- **Disable, don't fix.** `# noqa`, `// eslint-disable-line`, and rule
  exclusions in config turn findings into noise by decree. A rising ratio
  of suppressions to findings is the sensor telling you it is being
  overridden.
- **Rule-set erosion.** Teams start with a strict preset, then loosen one
  rule per fight until the linter agrees with everything. The linter still
  "passes" while detecting less.
- **Style-only drift.** If every enabled rule is stylistic, the linter
  becomes a formatting tax with no correctness value, which trains people
  to ignore it. The fix is the opposite of loosening: promote rules that
  catch real bug classes (unreachable code, unused results, suspicious
  comparisons) and demote the purely cosmetic ones.

The meta-signal is the suppression count. Track it like a metric, not a
lint error.

## What it cannot detect

A linter cannot detect [behavioral correctness](catalog.html#behavioral) —
it operates on syntax and patterns, not execution. It also produces false
positives, which erodes its authority over time.
