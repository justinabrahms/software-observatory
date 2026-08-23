---
id: SO-009d
title: Time-to-Repair
family: evolution
family_num: 09
oracle: medium
independence: high
scope: module
latency: weeks
actionability: exploratory
type: retrospective
stack_level: user-outcome
categories:
- Evolution
- Maintainability
- Black-Box Sensors
see_also:
- SO-009
- SO-009b
- SO-009c
last_reviewed: 2026-08-23
references:
- title: DORA
  url: https://dora.dev
  kind: tool
- title: Jira
  kind: tool
  url: https://www.atlassian.com/software/jira
  description: Project and issue tracking
- title: Linear
  kind: tool
  url: https://linear.app
  description: Issue tracking for product teams
- title: incident.io
  kind: tool
  url: https://incident.io
  description: Incident management and response platform
---

When this component breaks, how long does it take to restore? A sensor of
*maintainability* measured in hours, not in subjective assessment.

Time-to-repair (MTTR) measures how long it takes to fix a failure, from
detection to restoration. Long repair times indicate code that is difficult
to understand, debug, or safely modify — even if you don't know *why* it's
difficult.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — long repair time correlates with complexity |
| Independence | High — measured from incident records |
| Scope | Module-level |
| Feedback latency | Weeks |
| Actionability | Exploratory — shows where repair is slow |
| Type | Retrospective |

## What it cannot detect

Time-to-repair conflates code difficulty with operational factors (on-call
response time, deployment latency, test suite duration). A long repair time
may not reflect code quality at all.
