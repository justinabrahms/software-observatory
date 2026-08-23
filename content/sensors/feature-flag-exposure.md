---
id: SO-015
title: Feature Flag Exposure Telemetry
family: change
family_num: '07'
oracle: high
independence: high
scope: system
latency: seconds
actionability: guiding
type: retrospective
stack_level: production-behavior
categories:
- Change
- Production
see_also:
- SO-007
- SO-006c
- SO-012c
last_reviewed: 2026-08-23
references:
- title: Holistic Configuration Management at Facebook
  year: 2015
  tier: III
  url: https://sigops.org/s/conferences/sosp/2015/current/2015-Monterey/printable/008-tang.pdf
  kind: paper
- title: Development and Deployment at Facebook
  year: 2013
  tier: III
  url: https://www.cs.huji.ac.il/w~feit/papers/FB13IC.pdf
  kind: paper
- title: Feature flags
  url: https://martinfowler.com/articles/feature-toggles.html
  kind: tool
- title: LaunchDarkly
  kind: tool
  url: ''
  description: Feature management platform
- title: Statsig
  kind: tool
  url: ''
  description: Experimentation and feature flag platform
- title: GrowthBook
  kind: tool
  url: ''
  description: Open-source feature flagging and A/B testing
- title: Unleash
  kind: tool
  url: ''
  description: Open-source feature flag management
---

A change behind a flag is not a change anyone has experienced. Flag
evaluation streams answer "who is actually seeing the new behavior, right
now?" — the difference between *deployed* and *live*, and the ground truth
underneath every [canary analysis](canary-analysis.html) claim about a
rollout's state.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — evaluation events are direct records of what each request saw |
| Independence | High — emitted by the flag infrastructure, not the feature code |
| Scope | System |
| Feedback latency | Seconds |
| Actionability | Guiding — tells you the true exposure of a change |
| Type | Retrospective |

## What it cannot detect

Whether the new behavior is *correct* — only where it is *active*. Exposure
is the denominator; behavioral evidence still has to come from
[synthetic monitoring](synthetic-monitoring.html) or real traffic.
