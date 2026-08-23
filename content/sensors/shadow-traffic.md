---
id: SO-007b
title: Shadow Traffic
family: change
family_num: '07'
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
- SO-007
- SO-007c
- SO-005c
last_reviewed: 2026-08-23
references:
- title: Development and Deployment at Facebook
  year: 2013
  tier: III
  url: https://www.cs.huji.ac.il/w~feit/papers/FB13IC.pdf
  kind: paper
- title: Envoy shadow
  kind: tool
  url: ''
  description: Envoy proxy shadow traffic mirroring
- title: diffy
  kind: tool
  url: ''
  description: Differential proxy for API testing
- title: go-shadow
  kind: tool
  url: ''
  description: Go HTTP shadow traffic proxy
---

Run the new implementation against real inputs without affecting users. A
sensor that produces *differential evidence* with zero user risk.

Shadow traffic mirrors real requests to the new version, discards the
responses, and compares the new version's behavior to the old. It's
[differential testing](differential-testing.html) with real production
inputs.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — divergence on real inputs is strong evidence |
| Independence | High — production inputs |
| Scope | System-level |
| Feedback latency | Minutes |
| Actionability | Guiding — shows divergent requests and responses |
| Type | Retrospective |

## What it cannot detect

Shadow traffic can only compare what both versions produce. If both have
the same bug, it won't be detected. Also, side effects (database writes,
external calls) must be carefully isolated.
