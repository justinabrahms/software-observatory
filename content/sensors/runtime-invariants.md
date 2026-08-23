---
id: SO-004
title: Runtime Invariants
family: invariants
family_num: 4
oracle: high
independence: high
scope: system
latency: hours-seconds
actionability: guiding
type: retrospective
stack_level: production-behavior
categories:
- Invariants
- Domain Correctness
- Runtime Sensors
- Black-Box Sensors
see_also:
- SO-001
- SO-006
- adversarial
- behavioral-family
last_reviewed: 2026-08-23
references:
- title: 'Detecting Data Errors: Where are we and what needs to be done?'
  year: 2016
  tier: I
  url: https://www.vldb.org/pvldb/vol9/p993-abedjan.pdf
  kind: paper
- title: 'AddressSanitizer: A Fast Address Sanity Checker'
  year: 2012
  tier: III
  url: https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/37752.pdf
  kind: paper
- authors: Hoare
  title: An Axiomatic Basis for Computer Programming
  year: 1969
  kind: paper
- title: assertpy
  kind: tool
  url: https://github.com/assertpy/assertpy
  description: Python fluent assertion library
- title: pytest-check
  kind: tool
  url: https://github.com/fgaz/pytest-check
  description: Non-blocking assertions for pytest
- title: Hypothesis invariants
  kind: tool
  url: https://hypothesis.readthedocs.io/en/latest/quick-guide.html
  description: Using Hypothesis for invariant checking
---

You don't need to know how the payment service works. You can observe:
*"5,213 payments occurred; 17 have no corresponding order transition."* That's
a sensor of correctness without understanding the implementation. That is
enormously powerful.

## What must always be true

Instead of specifying examples — given X, expect Y — specify things that
must *always* be true. These are invariants, and they operate at multiple
levels:

```
account balance >= 0
order.total == sum(line_items)
created_at <= updated_at
every foreign key refers to an existing object
a successful payment implies an order eventually becomes paid
every request has exactly one request_id
```

Each invariant can be checked at compile time, test time, CI, runtime, in
the database, or in production analytics. Each is a different sensor at a
different cost point and latency.

> Runtime invariants become sensors of correctness without understanding
> the implementation. You don't need to read the code. You need to observe
> the event stream and ask: does this invariant hold?

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — a violation is definitive evidence of a bug |
| Independence | High — observes the system from outside |
| Scope | System-level (domain-level) |
| Feedback latency | Hours (batch) to seconds (real-time) |
| Actionability | Guiding — "17 payments have no order transition" |
| Type | Retrospective — detects violations after they occur |

## What it cannot detect

Runtime invariants can only check properties you *thought to specify*. They
don't find unknown unknowns — that's what [observability
events](observability-events.html) are for. They also can't tell you *why*
an invariant was violated, only that it was.
