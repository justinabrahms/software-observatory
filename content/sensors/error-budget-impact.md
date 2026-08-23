---
id: SO-007d
title: Error-Budget Impact
family: change
family_num: "07"
oracle: medium
independence: high
scope: system
latency: hours
actionability: guiding
type: retrospective
stack_level: user-outcome
categories:
  - Change
  - SLO
  - Production Sensors
see_also:
  - SO-007
  - SO-007b
  - evolution-family
last_reviewed: 2026-08-23
---

Did this change consume an abnormal amount of reliability budget? A sensor
that directly ties code changes to user-visible impact.

An error budget is the allowed amount of unreliability over a period (e.g.,
99.9% uptime = 43 minutes of downtime per month). Error-budget impact
measures whether a specific deployment consumed a disproportionate share of
that budget — connecting code changes to [user outcomes](catalog.html#evolution).

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — budget burn is correlated, not causal |
| Independence | High — production measurements |
| Scope | System-level |
| Feedback latency | Hours |
| Actionability | Guiding — "this deployment burned 30% of the monthly budget" |
| Type | Retrospective |

## What it cannot detect

Error-budget impact shows correlation between deployment and reliability
degradation, but not causation. Other factors (traffic patterns, upstream
failures) may contribute.
