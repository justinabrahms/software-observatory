---
id: SO-012b
title: Smoke Tests
family: behavioral
family_num: '02'
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
last_reviewed: 2026-08-23
references:
- title: 'Software Engineering at Google, ch. 11: Testing Overview'
  year: 2020
  tier: IV
  url: https://abseil.io/resources/swe-book/html/ch11.html
  kind: paper
- title: smoke-tester
  kind: tool
  url: ''
  description: Simple HTTP smoke testing
- title: curl-based smoke tests
  kind: tool
  url: ''
  description: Basic HTTP endpoint checks via curl
- title: k6 smoke
  kind: tool
  url: ''
  description: Smoke testing with k6 load testing tool
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
