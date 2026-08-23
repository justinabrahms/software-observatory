---
id: SO-003c-b
title: Branch Coverage
family: test-effectiveness
family_num: '03'
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
last_reviewed: 2026-08-23
references:
- title: Coverage Is Not Strongly Correlated with Test Suite Effectiveness
  year: 2014
  tier: I
  url: https://www.cs.ubc.ca/~rtholmes/papers/icse_2014.pdf
  kind: paper
- title: coverage.py
  kind: tool
  url: ''
  description: Python code coverage measurement
- title: Istanbul
  kind: tool
  url: ''
  description: JavaScript code coverage
- title: JaCoCo
  kind: tool
  url: ''
  description: Java code coverage
- title: gcov
  kind: tool
  url: ''
  description: GCC code coverage
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
