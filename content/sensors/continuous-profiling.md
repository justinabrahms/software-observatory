---
id: SO-006c
title: Continuous Profiling
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
- Profiling
- Production Sensors
see_also:
- SO-006
- SO-006b
- SO-006d
last_reviewed: 2026-08-23
references:
- title: Exploring Statistical Change Point Detection Techniques for Performance Anomaly
    Detection at Mozilla
  year: 2026
  tier: I
  url: https://arxiv.org/abs/2606.18377
  kind: paper
- title: 'FBDetect: Catching Tiny Performance Regressions at Hyperscale through In-Production
    Monitoring'
  year: 2024
  tier: III
  url: https://tangchq74.github.io/FBDetect-SOSP24.pdf
  kind: paper
- title: Pyroscope
  kind: tool
  url: ''
  description: Continuous profiling platform
- title: pprof
  kind: tool
  url: ''
  description: Go profiling tool
- title: Parca
  kind: tool
  url: ''
  description: Continuous profiling for Kubernetes
- title: Datadog Profiler
  kind: tool
  url: ''
  description: Always-on profiling in Datadog
---

Where did computation actually go? Not "CPU is 82%" but "this function
consumed 40% of the time in these specific requests." A sensor of *resource
reality*.

Continuous profiling samples production execution to show where CPU, memory,
allocations, and lock contention actually occur — not in synthetic
benchmarks, but in real traffic.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — shows where resources go, not whether it's correct |
| Independence | High — production samples |
| Scope | System-level |
| Feedback latency | Seconds |
| Actionability | Exploratory — you profile to find bottlenecks |
| Type | Retrospective |

## What it cannot detect

Profiling shows resource consumption, not [correctness](runtime-invariants.html).
A function that consumes 40% of CPU may be doing the wrong thing efficiently.
