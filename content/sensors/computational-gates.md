---
id: SO-011b
title: Computational Gates
family: ai-sensors
family_num: "11"
oracle: maximum
independence: maximum
scope: system
latency: seconds
actionability: guiding
type: predictive
stack_level: static-analysis
categories:
  - AI-Generated
  - Computational Controls
  - Maximum Oracle
see_also:
  - SO-011
  - SO-011c
  - SO-011d
---

An instruction saying "verify this" is weaker than a gate that literally
refuses to proceed unless the verification command succeeded. *Controls,
not rules.*

Computational gates are the enforcement mechanism: not "please run the
tests" but a CI pipeline that blocks merge if tests fail. Not "please check
types" but a build step that fails on type errors. The distinction between
prose rules and computational gates is critical for [agentic
coding](catalog.html#ai-sensors) — agents will skip prose rules if they
can.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Maximum — a gate is a fact, not a suggestion |
| Independence | Maximum — the gate is external to the agent |
| Scope | System-level |
| Feedback latency | Seconds (gate execution time) |
| Actionability | Guiding — the gate tells you exactly what failed |
| Type | Predictive |

## What it cannot detect

A gate can only enforce what it's configured to check. A gate that doesn't
exist can't block anything. The gap between "should be gated" and "is gated"
is invisible.
