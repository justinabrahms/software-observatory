---
id: SO-007
title: Canary Analysis
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
- SO-007b
- SO-007c
- SO-007d
- SO-005c
last_reviewed: 2026-08-23
references:
- title: Exploring Statistical Change Point Detection Techniques for Performance Anomaly
    Detection at Mozilla
  year: 2026
  tier: I
  url: https://arxiv.org/abs/2606.18377
  kind: paper
- title: Holistic Configuration Management at Facebook
  year: 2015
  tier: III
  url: https://sigops.org/s/conferences/sosp/2015/current/2015-Monterey/printable/008-tang.pdf
  kind: paper
- title: Netflix Kayenta
  url: https://github.com/spinnaker/kayenta
  kind: tool
- title: Kayenta
  kind: tool
  url: ''
  description: Netflix's automated canary analysis
- title: Argo Rollouts
  kind: tool
  url: ''
  description: Kubernetes progressive delivery
- title: Flagger
  kind: tool
  url: ''
  description: Kubernetes progressive delivery and canary
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
