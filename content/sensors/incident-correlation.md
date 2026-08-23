---
id: SO-009c
title: Incident Correlation
family: evolution
family_num: 09
oracle: medium
oracle_note: 'correlation, not causation'
independence: high
independence_note: 'incident data is external to the code'
scope: service
latency: weeks
actionability: exploratory
actionability_note: 'shows the correlation pattern'
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

## In practice

A typical reading is a quarter of incidents grouped by component:

| Component | Incidents (90d) | Share of SEV-2+ | Trend |
|-----------|-----------------|-----------------|-------|
| payments-worker | 7 | 38% | rising |
| session-cache | 3 | 16% | flat |
| search-indexer | 2 | 11% | falling |
| everything else | 6 | 33% | |

Reading it well:

- **Normalize by exposure.** A component that ships daily and carries the
  most traffic meets more opportunities to fail. Compare incidents per
  deploy or per request, not raw counts, before declaring a hotspot.
- **Distinguish cause from scene.** The component in the incident title
  is often where the symptom surfaced, not where the fault began. Read
  the postmortems before ranking.
- **Look for repeats.** One incident is an event; the same component
  failing in similar ways three times in a quarter is a structural
  weakness with a name on it.
- **Unreported incidents are dark matter.** The table only covers what
  got filed. If half the outages get fixed quietly, the ranking is built
  on the sample of teams that report.

## How it gets gamed

The sensor reads the incident record, so the record is what gets gamed:

- **Under-reporting.** Small outages get fixed in a chat and never filed,
  so the component's incident count stays clean. The correlation table
  then reflects reporting culture, not reliability.
- **Severity laundering.** A SEV-2 becomes a SEV-3 because "nobody was
  paged," or the incident gets logged as a maintenance note. Ranking by
  severity then ranks by willingness to label honestly.
- **Wrong-component attribution.** Filing the incident against the team
  that got paged instead of the component that broke spreads the risk
  away from the real hotspot.

The meta-signal is the filing rate: incidents filed per outage detected
by other sensors, such as [synthetic monitoring](synthetic-monitoring.html)
failures. Detected outages with no matching incident are dark matter.

## Response playbook

When correlation shows a component concentrating failures:

1. **Read the postmortems before acting.** Pull every incident the
   component appears in and check whether it was the cause or the scene.
   Correlation proposes; the write-ups dispose.
2. **Normalize by exposure.** Divide incidents by deploys and by traffic
   before comparing components; a hot component may just be the busiest
   one.
3. **Fund the hotspot.** The standard move is a reliability investment in
   the named component: better [runtime invariants](runtime-invariants.html),
   more [synthetic monitoring](synthetic-monitoring.html) around it, or a
   dedicated hardening sprint. Risk concentration is a budgeting signal.
4. **Decide whether to isolate.** If the component keeps failing and
   cannot be hardened quickly, wrap it: bulkheads, timeouts, fallbacks,
   so its failures stop cascading. Containment is the honest alternative
   to pretending the correlation will improve on its own.
5. **Re-run the correlation next quarter.** If the investment worked, the
   component's share should fall. If it did not, the diagnosis was wrong
   or the fix was cosmetic.

## What it cannot detect

Incident correlation can't tell you *why* a component fails — only that it
does. Also depends on incident reporting quality: unreported incidents
produce no signal.
