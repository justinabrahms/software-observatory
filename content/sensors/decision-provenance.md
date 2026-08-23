---
id: SO-010d
title: Decision Provenance
family: comprehension
family_num: "10"
oracle: low
independence: high
scope: module
latency: days
actionability: exploratory
type: retrospective
stack_level: static-analysis
categories:
  - Comprehension
  - Archaeological Accessibility
see_also:
  - SO-010
  - SO-010b
  - SO-010c
last_reviewed: 2026-08-23
---

Can you answer "why is this weird thing here?" A sensor of *archaeological
accessibility* — can you determine why code exists, not just what it does?

Decision provenance traces the history of a design decision: the ADRs, PRs,
discussions, and constraints that led to the current code. When provenance
is lost, the code becomes untouchable — nobody knows whether it can be
changed safely.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Low — missing provenance is a risk factor |
| Independence | High — history is independent of current code |
| Scope | Module-level |
| Feedback latency | Days |
| Actionability | Exploratory — shows whether provenance exists |
| Type | Retrospective |

## What it cannot detect

Decision provenance can only exist where decisions were *recorded*. Decisions
made verbally, in deleted branches, or in private messages are invisible to
this sensor.
