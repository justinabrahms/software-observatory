---
id: SO-009c
title: Incident Correlation
family: evolution
family_num: 09
oracle: medium
independence: high
scope: service
latency: weeks
actionability: exploratory
type: retrospective
stack_level: user-outcome
categories:
- Evolution
- Operational Risk
- Black-Box Sensors
see_also:
- SO-009
- SO-009b
- SO-009d
- SO-006
last_reviewed: 2026-08-23
references:
- title: How to Fight Production Incidents? An Empirical Study on a Large-scale Cloud
    Service
  year: 2022
  tier: II
  url: https://acmsocc.org/2022/assets/slides/95.pdf
  kind: paper
- title: Postmortem of database outage of January 31
  year: 2017
  tier: III
  url: https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/
  kind: paper
- title: Datadog
  kind: tool
  url: https://www.datadoghq.com
  description: Cloud monitoring and observability
- title: Sentry
  kind: tool
  url: https://sentry.io
  description: Error tracking and crash reporting
- title: Jira correlation
  kind: tool
  url: https://support.atlassian.com/jira-software-cloud/docs/what-is-issue-linking/
  description: Incident-to-commit correlation via Jira
---

Which components correlate with production failures? A sensor of operational
risk concentration, measured from [observability events](observability-events.html).

Incident correlation maps production incidents to the components they
involve. Components that appear disproportionately often in incident reports
are risk concentrations — places where the system is most likely to fail.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — correlation, not causation |
| Independence | High — incident data is external to the code |
| Scope | Service-level |
| Feedback latency | Weeks |
| Actionability | Exploratory — shows the correlation pattern |
| Type | Retrospective |

## What it cannot detect

Incident correlation can't tell you *why* a component fails — only that it
does. Also depends on incident reporting quality: unreported incidents
produce no signal.
