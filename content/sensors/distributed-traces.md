---
id: SO-006b
title: Distributed Traces
family: runtime
family_num: "06"
oracle: medium
independence: high
scope: system
latency: seconds
actionability: exploratory
type: retrospective
stack_level: production-behavior
categories:
  - Runtime
  - Traces
  - Production Sensors
see_also:
  - SO-006
  - SO-006c
  - SO-006d
  - change-family
last_reviewed: 2026-08-23
---

What path did this particular operation take? A sensor of *execution flow*
across service boundaries — the span tree is itself a signal.

A trace shows you the actual path a request took through your system:
which services were called, in what order, how long each took. Where
[observability events](observability-events.html) give you per-execution
facts, traces give you the *shape* of execution.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — shows what happened, not whether it was correct |
| Independence | High — production reality |
| Scope | System-level |
| Feedback latency | Seconds |
| Actionability | Exploratory — you trace to find the signal |
| Type | Retrospective |

## What it cannot detect

Traces show execution paths but not [correctness](runtime-invariants.html).
A trace that completes successfully may still violate a business invariant.
Pair traces with [invariant checking](runtime-invariants.html) for
correctness signal.

## Tooling

- OpenTelemetry
- Jaeger
- Zipkin
- Tempo

## References

- The Tail at Scale (2013, tier III) — https://www.barroso.org/publications/TheTailAtScale.pdf

- Dapper paper: https://research.google/pubs/pub36356/