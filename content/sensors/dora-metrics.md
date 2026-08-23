---
id: SO-015b
title: DORA Metrics
family: evolution
family_num: "09"
oracle: medium
independence: high
scope: organization
latency: days
actionability: guiding
type: retrospective
stack_level: canary-shadow
categories:
  - Evolution
  - Delivery Performance
see_also:
  - SO-009
  - SO-009b
  - SO-009d
last_reviewed: 2026-08-23
---

Deployment frequency, lead time for changes, change failure rate, time to
restore. Four numbers about how changes have historically flowed through
this organization — a sensor of delivery *pattern*, answering "does our
recent past look like teams that ship safely?"

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — the metrics proxy safety; they are not safety |
| Independence | High — derived from deployment and incident records, not self-report |
| Scope | Organization |
| Feedback latency | Days |
| Actionability | Guiding — tells you which stage of the pipeline to distrust |
| Type | Retrospective |

## What it cannot detect

The cause of a bad number. DORA metrics locate the problem in time and
stage; understanding it requires [decision provenance](decision-provenance.html)
and [incident correlation](incident-correlation.html). And like all metrics
that become targets, they invite gaming — deployment frequency can be raised
by shipping trivia.
