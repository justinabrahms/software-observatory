---
id: SO-004c
title: Business Invariants
family: invariants
family_num: '04'
oracle: high
independence: high
scope: system
latency: hours
actionability: guiding
type: retrospective
stack_level: user-outcome
categories:
- Invariants
- Domain Correctness
- Black-Box Sensors
see_also:
- SO-004
- SO-004b
- SO-006
last_reviewed: 2026-08-23
references:
- title: Great Expectations
  url: https://greatexpectations.io
  kind: tool
  description: Python data quality testing
- title: Soda
  kind: tool
  url: https://docs.soda.io
  description: Data quality testing and monitoring
- title: dbt tests
  kind: tool
  url: https://docs.getdbt.com/docs/build/tests
  description: Data transformation testing
---

A successful payment implies an order eventually becomes paid.
`order.total == sum(line_items)`. These are *domain-level correctness*
sensors that need no knowledge of the implementation.

Business invariants are the highest-level invariant sensor: they check
whether the system is accomplishing its business purpose, not just whether
its internals are consistent. They require [observability
events](observability-events.html) as a data source.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — a violation means the business is broken |
| Independence | High — observes outcomes, not implementation |
| Scope | System-level (domain-level) |
| Feedback latency | Hours |
| Actionability | Guiding — "17 payments have no order transition" |
| Type | Retrospective |

## What it cannot detect

Business invariants can only check properties you *thought to specify*. They
don't find unknown unknowns — that's what [observability](observability-events.html)
is for.
