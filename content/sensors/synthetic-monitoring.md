---
id: SO-012c
title: Synthetic Monitoring
family: behavioral
family_num: "02"
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

## Tooling

- Checkly
- k6
- Pingdom
- Datadog Synthetic

## References

- Meaningful Availability (2020, tier III) — https://www.usenix.org/system/files/nsdi20-paper-hauer.pdf
- Monitoring Distributed Systems (SRE Book, ch. 6) (2016, tier IV) — https://sre.google/sre-book/monitoring-distributed-systems/

- Checkly: https://checklyhq.com