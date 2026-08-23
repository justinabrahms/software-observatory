---
id: SO-007
title: Canary Analysis
family: change
family_num: "07"
oracle: high
independence: high
scope: system
latency: minutes
actionability: guiding
type: retrospective
stack_level: canary-shadow
categories:
  - Change
  - Deployment Safety
see_also:
  - SO-007b
  - SO-007c
  - SO-007d
  - SO-005c
last_reviewed: 2026-08-23
---

Does the new version behave differently from the old version? A sensor of
*behavioral drift* between deployments, measured on real traffic.

Canary analysis routes a small percentage of production traffic to the new
version and compares its behavior to the old. If error rates, latency, or
[invariant violations](runtime-invariants.html) diverge, the canary fails.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — divergence on real traffic is strong evidence |
| Independence | High — production behavior cannot be gamed |
| Scope | System-level |
| Feedback latency | Minutes |
| Actionability | Guiding — shows which metrics diverged |
| Type | Retrospective |

## What it cannot detect

Canary analysis can only detect differences in metrics you're measuring.
Unknown unknowns require [high-cardinality events](observability-events.html)
to investigate after the fact.

## Tooling

- Kayenta
- Argo Rollouts
- Flagger

## References

- Netflix Kayenta: https://github.com/spinnaker/kayenta
