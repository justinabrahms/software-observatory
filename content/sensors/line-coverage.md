---
id: SO-003c
title: Line Coverage
family: test-effectiveness
family_num: "03"
oracle: low
independence: low
scope: line
latency: seconds
actionability: guiding
type: predictive
stack_level: behavioral-tests
categories:
  - Test Effectiveness
  - Coverage
see_also:
  - SO-003c-b
  - SO-003
  - SO-003b
last_reviewed: 2026-08-23
---

Did we execute this line? Useful but weak. A project can have 90% line
coverage while [mutation testing](mutation-testing.html) finds large numbers
of mutations that tests don't detect.

Coverage measures execution. An assertion measures correctness. These are
not the same thing.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Low — execution is not correctness |
| Independence | Low — same author writes tests |
| Scope | Line-level |
| Feedback latency | Seconds |
| Actionability | Guiding — shows which lines weren't executed |
| Type | Predictive |

## What it cannot detect

Whether the code that *executed* was actually *asserted on*. A line can
execute without any test verifying its output. This is why coverage alone
is a [weak oracle](mutation-testing.html).

## Tooling

- coverage.py
- Istanbul
- JaCoCo
- gcov

## References

- Coverage Is Not Strongly Correlated with Test Suite Effectiveness (2014, tier I) — https://www.cs.ubc.ca/~rtholmes/papers/icse_2014.pdf
- Does Mutation Testing Improve Testing Practices? (2021, tier I) — https://homes.cs.washington.edu/~rjust/publ/mutation_testing_practices_icse_2021.pdf

- https://martinfowler.com/bliki/TestCoverage.html