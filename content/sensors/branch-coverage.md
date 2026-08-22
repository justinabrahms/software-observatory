---
id: SO-003c-b
title: Branch Coverage
family: test-effectiveness
family_num: "03"
oracle: low
independence: low
scope: function
latency: seconds
actionability: guiding
type: predictive
stack_level: behavioral-tests
categories:
  - Test Effectiveness
  - Coverage
see_also:
  - SO-003c
  - SO-003
  - SO-003b
---

Did we exercise both sides of decisions? Better than [line
coverage](line-coverage.html). Path coverage is better still, but usually
expensive and impractical at scale.

Branch coverage catches the case where a conditional's true path is tested
but the false path is not — a common gap that line coverage misses because
the line containing the branch executes either way.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Low — execution is not correctness |
| Independence | Low — same author writes tests |
| Scope | Function-level |
| Feedback latency | Seconds |
| Actionability | Guiding — shows which branches weren't exercised |
| Type | Predictive |

## What it cannot detect

Same limitations as [line coverage](line-coverage.html) — execution is not
assertion. Branch coverage tells you the branch ran, not that the right
thing happened when it did.
