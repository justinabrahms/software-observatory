---
id: SO-006
title: Observability Events
family: runtime
family_num: 06
oracle: medium
independence: high
scope: system
latency: seconds
actionability: exploratory
type: retrospective
stack_level: production-behavior
categories:
  - Runtime
  - High Cardinality
  - Events
  - Production Sensors
see_also:
  - SO-004
  - change-family
  - evolution-family
  - ai-sensors
last_reviewed: 2026-08-23
---

Traditional monitoring says: *"CPU is 82%."* Observability says: *"Show me
the requests that are slow, and let me figure out what those requests have
in common."*

The distinction is fundamental. Monitoring collects predetermined health
metrics. Observability preserves enough information to ask questions you
didn't know you would need to ask. The implementation emphasizes wide
structured events, high cardinality, high dimensionality, retained context,
and exploratory querying.

## The event as the fundamental unit

Make events the center rather than metrics. A metric is a pre-aggregation of
reality. An event is a fact about one execution, with enough context to
investigate it.

```
checkout.completed
  user_id:        u_8473
  cart_id:        c_29201
  order_id:       o_14829
  deployment:     deploy-2026-08-22-a
  git_sha:        a1b2c3d
  experiment:     checkout_v2
  payment_provider: stripe
  duration:       1.8s
  db_queries:     23
  cache_hits:     7
  region:         us-east-1
```

The sensor isn't `checkout latency = 1.8s`. It's: *here is an observable fact
about one execution, with enough context to investigate it.* That's a much
richer sensor.

> The Honeycomb conception of observability provides the other half of the
> sensor model: don't merely collect predetermined health metrics; preserve
> enough information to ask questions you didn't know you would need to ask.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — shows what happened, not whether it was correct |
| Independence | High — production reality cannot be gamed by the test author (but the producer chose what to instrument) |
| Scope | System-level |
| Feedback latency | Seconds (real-time) |
| Actionability | Exploratory — you query to find the signal |
| Type | Retrospective — what actually happened |

## What it cannot detect

Observability events tell you *what happened*, not *whether it was correct*.
Determining correctness requires [invariants](runtime-invariants.html) layered
on top of events. Events without invariants are raw data, not yet sensors of
correctness.
