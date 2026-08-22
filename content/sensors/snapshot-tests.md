---
id: SO-002d
title: Snapshot Tests
family: behavioral
family_num: "02"
oracle: medium
independence: low
scope: function
latency: seconds
actionability: guiding
type: predictive
stack_level: behavioral-tests
categories:
  - Behavioral
  - Drift Detection
see_also:
  - SO-002b
  - SO-002c
  - SO-003
---

Did observable output change? Not "is it correct" but "did it change" — a
sensor for detecting *unintended drift* in externally observable artifacts.

Snapshot tests (also called golden master or approval tests) record a
canonical output and fail when it changes. They're particularly useful when
you don't know what the correct output is, but you know it shouldn't change
without intention.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — change is detected, correctness is not |
| Independence | Low — same author creates the snapshot |
| Scope | Function-level |
| Feedback latency | Seconds |
| Actionability | Guiding — shows the diff between old and new output |
| Type | Predictive |

## What it cannot detect

Snapshot tests can't tell you whether the *original* snapshot was correct.
They only detect *change*, not *correctness*. Also prone to "approve all"
fatigue when outputs are large.
