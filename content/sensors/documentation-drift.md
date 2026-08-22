---
id: SO-010b
title: Documentation Drift
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
  - Documentation
see_also:
  - SO-010
  - SO-010c
  - SO-010d
---

Does documentation still predict behavior? A sensor of the gap between what
the system is documented to do and what it *actually* does.

Documentation drift measures whether the docs match reality. When they
diverge, the documentation becomes a liability: it misleads rather than
guides. Detecting drift requires comparing documented behavior to
[observed behavior](observability-events.html) or [test
assertions](example-based-tests.html).

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Low — drift is a risk factor, not a bug |
| Independence | High — docs and code are independent artifacts |
| Scope | Module-level |
| Feedback latency | Days |
| Actionability | Exploratory — shows the gap |
| Type | Retrospective |

## What it cannot detect

Documentation drift can only be detected where documentation exists.
Undocumented behavior is invisible to this sensor.
