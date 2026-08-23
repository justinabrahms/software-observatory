---
id: SO-012d
title: Escaped Defect Rate
family: test-effectiveness
family_num: "03"
oracle: medium
independence: high
scope: system
latency: weeks
actionability: guiding
type: retrospective
stack_level: user-outcome
categories:
  - Test Effectiveness
  - Quality Outcomes
see_also:
  - SO-003
  - SO-009c
  - SO-012c
last_reviewed: 2026-08-23
---

Of the bugs that reached users, which ones should the test suite have
caught? Escaped defect rate is the slowest and most honest measure of test
effectiveness: not "would the tests catch a hypothetical mutant?" but "did
they catch the actual failures, judged after the fact?"

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — classification of "should have caught" is judgment |
| Independence | High — production failures cannot be gamed by the suite |
| Scope | System |
| Feedback latency | Weeks |
| Actionability | Guiding — points at the layers of the suite that leak |
| Type | Retrospective |

## What it cannot detect

Defects nobody reported, and defects attributed to the wrong cause. It also
lags badly: it tells you about the suite you had, not the suite you have.
Pair it with [mutation testing](mutation-testing.html) for a fast proxy and
with [incident correlation](incident-correlation.html) for the cost side.
