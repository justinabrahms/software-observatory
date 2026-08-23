---
id: SO-006b
title: Distributed Traces
family: runtime
family_num: '06'
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
references:
- title: The Tail at Scale
  year: 2013
  tier: III
  url: https://www.barroso.org/publications/TheTailAtScale.pdf
  kind: paper
- title: Dapper paper
  url: https://research.google/pubs/pub36356/
  kind: tool
- title: OpenTelemetry
  kind: tool
  url: ''
  description: Open-standard observability instrumentation
- title: Jaeger
  kind: tool
  url: ''
  description: Distributed tracing backend
- title: Zipkin
  kind: tool
  url: ''
  description: Distributed tracing system
- title: Tempo
  kind: tool
  url: ''
  description: Grafana-backed distributed tracing
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
