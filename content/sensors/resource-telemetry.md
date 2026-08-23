---
id: SO-006d
title: Resource Telemetry
family: runtime
family_num: "06"
oracle: low
independence: high
scope: system
latency: seconds
actionability: exploratory
type: retrospective
stack_level: production-behavior
categories:
  - Runtime
  - Monitoring
see_also:
  - SO-006
  - SO-006b
  - SO-006c
last_reviewed: 2026-08-23
---

CPU, memory, IO, network, GC, queues. Traditional monitoring — useful but
limited. Low cardinality, low dimensionality, predetermined questions.

Resource telemetry is the weakest runtime sensor. It tells you aggregate
system state ("CPU is 82%") but not *which* requests or *which* code paths
caused it. [Observability events](observability-events.html) are a strictly
richer sensor — they preserve the per-request context that telemetry
discards.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Low — aggregate state, not causation |
| Independence | High — production reality |
| Scope | System-level |
| Feedback latency | Seconds |
| Actionability | Exploratory — but low dimensionality limits investigation |
| Type | Retrospective |

## What it cannot detect

Resource telemetry cannot tell you *why* resources are consumed or *which*
requests are responsible. It shows aggregate state, not per-execution
reality. This is why [observability events](observability-events.html) are a
strictly richer sensor.
