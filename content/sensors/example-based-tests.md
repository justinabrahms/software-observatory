---
id: SO-002b
title: Example-Based Tests
family: behavioral
family_num: "02"
oracle: high
independence: low
scope: function
latency: seconds
actionability: guiding
type: predictive
stack_level: behavioral-tests
categories:
  - Behavioral
  - Guiding Sensors
see_also:
  - SO-002c
  - SO-002d
  - SO-003
last_reviewed: 2026-08-23
---

Given X, expect Y. The fundamental behavioral sensor.

Fundamentally different from [coverage](diff-coverage.html): coverage says
"this code executed." A behavioral assertion says "this code produced the
*right result*." That is a massive distinction.

## The weakness

Example-based tests are only as good as the examples chosen. They test what
the author thought to test. [Mutation testing](mutation-testing.html) and
[metamorphic testing](metamorphic-testing.html) exist to find the gaps.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — assertion failure is definitive |
| Independence | Low — same author writes code and tests |
| Scope | Function-level |
| Feedback latency | Seconds |
| Actionability | Guiding — shows expected vs actual |
| Type | Predictive |

## What it cannot detect

Missing behavior, untested edge cases, and [integration
failures](contract-tests.html) that emerge only when components are
connected.

## Tooling

- pytest
- Jest
- JUnit
- Go testing

## References

- Beizer, 'Software Testing Techniques' (1990)
