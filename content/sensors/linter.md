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
last_reviewed: '2026-08-28'
references:
- title: 'Gang of Eight: A Defect Taxonomy for Infrastructure as Code Scripts'
  year: 2020
  tier: II
  url: https://akondrahman.github.io/files/papers/icse20_acid.pdf
  kind: publication
  authors: Akond Rahman, Effat Farhana, Chris Parnin, Laurie Williams
  venue: ICSE 2020
- title: 'The Seven Sins: Security Smells in Infrastructure as Code Scripts'
  year: 2019
  tier: II
  url: https://akondrahman.github.io/files/papers/icse19_slic.pdf
  kind: publication
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

Linters and type checkers usually inspect source independently; there is no
fixed pipeline position between type checking and compilation. A linter's
rules may identify likely defects or enforce a convention. The rule and
context determine how much authority a finding deserves. Compilers can
also be wrong; [differential testing](differential-testing.html) is one way
to find their defects.

## In practice

Illustrative finding, not a particular linter's console output:

```text
Rule: unused-result
Location: checkout.py:42
Finding: the result of calculate_total(order) is discarded
```

Read the call and its contract before accepting the finding. If the caller
needed the returned total, discarding it is a bug. If the call exists for a
side effect and its return value is optional, the rule may be too broad.
A location makes the finding easy to inspect; it does not settle that
judgment.

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
  becomes a formatting tax with no correctness value, and people learn to
  ignore the whole tool — including the rules that were worth reading.
  The answer is not to loosen it. Formatting should not be in the linter
  at all: hand it to an autoformatter that rewrites the file without
  asking, so nobody spends attention on it, and keep the linter for rules
  that catch real bug classes — unreachable code, unused results,
  suspicious comparisons. A linter arguing about brace placement is
  occupying a slot a tool would have silently fixed.

The meta-signal is the suppression count. Track it like a metric, not a
lint error.

## Response playbook

1. **Read the rule and the surrounding code.** Decide whether it identifies
   a real defect, a style disagreement, or a limitation in the analyzer.
2. **Fix the code when the finding is right.** Use an automatic fix only
   after inspecting what it changes, then run the relevant tests.
3. **Keep justified exceptions local.** State why the rule is wrong for
   this line and suppress that finding rather than disabling the rule
   across the project.
4. **Review recurring noise.** If the same rule is repeatedly suppressed,
   check its configuration and whether another check covers the failure
   mode before changing the shared preset.

## What it cannot detect

A linter cannot detect [behavioral correctness](catalog.html#behavioral) —
it operates on syntax and patterns, not execution. It also produces false
positives, which erodes its authority over time.
