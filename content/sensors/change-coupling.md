---
id: SO-009b
title: Change Coupling
family: evolution
family_num: "09"
oracle: medium
independence: high
scope: system
latency: days
actionability: exploratory
type: retrospective
stack_level: static-analysis
categories:
  - Evolution
  - Hidden Coupling
  - Black-Box Sensors
see_also:
  - SO-009
  - SO-009c
  - SO-009d
  - SO-008
last_reviewed: 2026-08-23
---

Which files repeatedly change together? A sensor of *hidden coupling* — the
repository itself becomes a sensor, no code reading required.

Change coupling reveals relationships the [dependency
graph](dependency-graph.html) can't see: modules that have no structural
dependency but always change together. This is often a sign of shared
business rules, duplicated logic, or implicit coordination.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — coupling correlates with risk |
| Independence | High — computed from git history |
| Scope | System-level |
| Feedback latency | Days |
| Actionability | Exploratory — shows the coupling clusters |
| Type | Retrospective |

## What it cannot detect

Change coupling shows correlation, not causation. Files that change together
may do so for coincidental reasons (same sprint, same author) rather than
structural coupling.
