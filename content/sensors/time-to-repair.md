---
id: SO-009d
title: Time-to-Repair
family: evolution
family_num: 09
oracle: medium
oracle_note: 'long repair time correlates with complexity'
independence: high
independence_note: 'measured from incident records'
scope: module
latency: weeks
actionability: exploratory
actionability_note: 'shows where repair is slow'
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

## In practice

A time-to-repair reading is an incident record collapsed to a duration,
usually on a dashboard next to the component it concerns:

| Incident | Component | Detected | Restored | Duration |
|----------|-----------|----------|----------|----------|
| INC-412 | billing | 09:14 | 15:52 | 6h 38m |
| INC-418 | billing | 13:02 | 14:11 | 1h 9m |
| median MTTR, billing, 90 days | | | | **3h 40m** |

The number is a median across incidents, not a single event. Reading it
well:

1. **Read the median, then read the tail.** A 3h median with a 26h
   worst case means most repairs are routine and some are catastrophic.
   The tail is where the hard code lives.
2. **Decompose before judging.** Time-to-repair is detection plus
   diagnosis plus fix plus deploy. A long MTTR caused by a 2-hour
   deploy pipeline is an operational problem, not a code problem.
3. **Compare components on the same scale.** Billing at 3h and search
   at 40 minutes says something about the two codebases, provided
   their incident volumes and on-call setups are comparable.
4. **Treat the trend as the sensor.** MTTR is noisy incident to
   incident. The reading that matters is whether repairs in this area
   are getting slower over quarters, which is the maintainability
   drift this sensor exists to catch.

## How it gets gamed

MTTR is computed from timestamps in incident records, and every one of
those timestamps can be massaged:

- **Closing the incident early.** The clock stops when the incident is
  marked resolved, so declaring victory at mitigation and logging the
  remaining work as a follow-up produces a short MTTR while users keep
  hurting. The metric improves; the repair did not finish.
- **Delaying detection to shrink the window.** If the start time is
  "first alert" rather than "first user impact," an hour of silent
  failure disappears from the number. The repair looks faster because
  the clock started late.
- **Splitting one incident into several.** Two 2-hour incidents look
  better than one 4-hour incident in the median, and the split is
  always justifiable after the fact.

The meta-signal is the gap between mitigation time and full-restoration
time per incident. When the gap grows while MTTR falls, incidents are
being closed at the workaround, not at the fix.

## Response playbook

When repair times climb or a single incident runs long:

1. **Decompose the timeline after the fact.** Split detection,
   diagnosis, fix, and deployment. The longest segment is the target,
   and each segment has a different fix.
2. **Attack the diagnosis segment first.** If most of the time went to
   finding the cause, the code lacks legibility: add
   [observability](observability-events.html) and runbooks for the
   failure modes that just cost hours.
3. **Make the fix safe to deploy.** If repair waited on a slow pipeline
   or a risky deploy, that is the bottleneck to remove: faster
   rollbacks, smaller releases, a rehearsed revert path.
4. **Write the regression test from the incident.** The failure that
   took hours to repair is a free test case. Land it before the next
   incident in the same area.
5. **Track MTTR per component, not per team.** Team-level MTTR invites
   the gaming above; component-level MTTR points at the code that is
   hard to repair, which is what the sensor is for.

## What it cannot detect

Time-to-repair conflates code difficulty with operational factors (on-call
response time, deployment latency, test suite duration). A long repair time
may not reflect code quality at all.
