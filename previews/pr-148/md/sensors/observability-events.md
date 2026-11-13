---
id: SO-006
title: Observability Events
family: runtime
family_num: 6
oracle: medium
oracle_note: shows what happened, not whether it was correct
independence: high
independence_note: production reality cannot be gamed by the test author (but the producer chose what to instrument)
scope: system
latency: seconds
latency_note: real-time
actionability: exploratory
actionability_note: you query to find the signal
type: retrospective
type_note: what actually happened
stack_level: production-behavior
categories:
- Runtime
- Production Sensors
see_also:
- SO-004
- SO-006b
- change
- evolution
- comprehension
references:
- title: How to Fight Production Incidents? An Empirical Study on a Large-scale Cloud Service
  year: 2022
  tier: II
  url: https://acmsocc.org/2022/assets/slides/95.pdf
  kind: publication
  authors: Supriyo Ghosh, Manish Shetty, Chetan Bansal, Suman Nath
  venue: ACM SoCC '22
- title: The Tail at Scale
  year: 2013
  tier: III
  url: https://www.barroso.org/publications/TheTailAtScale.pdf
  kind: publication
  authors: Jeffrey Dean, Luiz André Barroso
  venue: Communications of the ACM 56(2)
- authors: Charity Majors et al.
  title: Observability Engineering
  year: 2022
  kind: publication
  tier: IV
- title: OpenTelemetry
  url: https://opentelemetry.io
  kind: tool
  description: Open-standard observability instrumentation
- title: Honeycomb
  kind: tool
  url: https://www.honeycomb.io
  description: Observability platform for high-cardinality events
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

## In practice

A typical reading starts from a symptom and slices until one dimension
explains it. "p99 checkout duration is up" becomes a query grouped by
deployment and payment provider:

| deployment | provider | p99 duration | requests | error rate |
|------------|----------|--------------|----------|------------|
| deploy-08-21-a | stripe | 1.9s | 41,203 | 0.1% |
| deploy-08-22-a | stripe | 4.7s | 39,877 | 0.9% |
| deploy-08-22-a | paypal | 2.0s | 12,044 | 0.1% |

The symptom exists in one deployment, on one provider. The cohort is the
finding.

Reading it well:

- **Slice until the variance lives in one dimension.** If every dimension
  shows the same degradation, the cause is below the event layer: hosts,
  network, a shared dependency. If one value carries it, you have a
  handle.
- **Keep the identifying fields.** `user_id`, `request_id`, and `git_sha`
  are what let an event join to a complaint, a trace, and a deploy.
  Events stripped of identifiers aggregate back into telemetry.
- **Sample with suspicion.** If events are sampled, know which ones
  survive. Head sampling drops errors at the same rate as successes, so
  the worst executions become precisely the ones you cannot see.

## How it gets gamed

Events are emitted by the same teams that ship the code, so the sensor
can be degraded at the source:

- **Sampling away the inconvenient.** Head-based sampling drops errors at
  the same rate as successes, so the worst executions are precisely the
  ones missing when you go looking. Tail-based sampling that keeps
  errors is the honest configuration.
- **Cardinality starvation.** "Stop emitting user_id, it's blowing up
  our bill" is sometimes a real cost decision and sometimes a way to
  make a per-user abuse pattern unqueryable. Every dropped field is a
  question the team can no longer answer.
- **Instrumentation theater.** A service that emits one `request.done`
  event with no fields technically participates in observability while
  telling you nothing. Coverage counts without field checks reward this.

The meta-signal is event volume per service, tracked over time. A service
whose event rate falls after a contentious incident is a sensor being
turned down.

## Response playbook

When an event query reveals a bad cohort, for example one deployment
and one provider carrying all the errors:

1. **Reproduce the query and pin the cohort.** Save the exact query, the
   time window, and the filter values that isolate the problem. A cohort
   you cannot re-derive is a rumor.
2. **Pull raw events for the victims.** Download a handful of the
   failing events with their identifiers and join them to
   [distributed traces](distributed-traces.html) and error reports; the
   fields on one bad event usually name the mechanism.
3. **Confirm the blast radius.** Count affected users, requests, and
   regions from the same events before deciding between a fix-forward
   and a rollback.
4. **Contain via the deploy, not the symptom.** If the cohort correlates
   with a deployment or a feature flag, revert or disable it. Fixing
   forward while the cohort keeps growing is paying interest.
5. **Close the instrumentation gap.** If the investigation stalled on a
   missing field, add it before the next incident, while the pain is
   still the argument.

## What it cannot detect

Observability events tell you *what happened*, not *whether it was correct*.
Determining correctness requires [invariants](runtime-invariants.html) layered
on top of events. Events without invariants are raw data, not yet sensors of
correctness.
