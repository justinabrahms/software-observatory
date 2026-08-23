---
id: SO-012c
title: Synthetic Monitoring
family: behavioral
family_num: '02'
oracle: high
independence: high
scope: system
latency: minutes
actionability: guiding
type: retrospective
stack_level: production-behavior
categories:
- Behavioral
- Production
see_also:
- SO-006c
- SO-007
- SO-012b
last_reviewed: 2026-08-23
references:
- title: Meaningful Availability
  year: 2020
  tier: III
  url: https://www.usenix.org/system/files/nsdi20-paper-hauer.pdf
  kind: paper
- title: Monitoring Distributed Systems (SRE Book, ch. 6)
  year: 2016
  tier: IV
  url: https://sre.google/sre-book/monitoring-distributed-systems/
  kind: paper
- title: Checkly
  url: https://checklyhq.com
  kind: tool
  description: Synthetic monitoring as code
- title: k6
  kind: tool
  url: ''
  description: Open-source load testing tool
- title: Pingdom
  kind: tool
  url: ''
  description: Uptime and performance monitoring
- title: Datadog Synthetic
  kind: tool
  url: ''
  description: Synthetic monitoring in Datadog
---

Scripted user flows run against the production system around the clock:
log in, search, add to cart, check out. Synthetic monitoring is a behavioral
test suite whose environment is the real world, giving you a baseline answer
to "does it do what we expect?" even when no user happens to be asking.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — a failed checkout flow is unambiguous |
| Independence | High — runs outside the system, against its public surface |
| Scope | System |
| Feedback latency | Minutes |
| Actionability | Guiding — the failing step localizes the breakage |
| Type | Retrospective |

## What it cannot detect

Behavior outside the scripted paths. Synthetics cover the flows you thought
to script; the long tail of user behavior is the domain of
[observability events](observability-events.html) and real-user monitoring.
