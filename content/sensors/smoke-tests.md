---
id: SO-012b
title: Smoke Tests
family: behavioral
family_num: "02"
oracle: medium
independence: high
scope: system
latency: seconds
actionability: blocking
type: retrospective
stack_level: canary-shadow
categories:
  - Behavioral
  - Deployment Safety
see_also:
  - SO-002c
  - SO-007
  - SO-013b
---

The cheapest behavioral check against a live deployment: hit `/health`,
create one record, read it back, delete it. If any step fails, roll back.
Smoke tests answer "is the deployed system alive enough to behave at all?"
before [canary analysis](canary-analysis.html) has enough traffic to judge.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — "alive" is a weak claim, but a true one |
| Independence | High — exercises the real deployed artifact end to end |
| Scope | System |
| Feedback latency | Seconds |
| Actionability | Blocking — a failed smoke test halts the rollout |
| Type | Retrospective |

## What it cannot detect

Anything that requires real load, real data shapes, or real user behavior.
A smoke test passing is necessary for the deployment to proceed and
sufficient for almost nothing else.
