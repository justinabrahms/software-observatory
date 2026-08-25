---
id: SO-006b
title: Distributed Traces
family: runtime
family_num: '06'
oracle: medium
oracle_note: shows what happened, not whether it was correct
independence: high
independence_note: production reality
scope: system
latency: seconds
actionability: exploratory
actionability_note: you trace to find the signal
type: retrospective
stack_level: production-behavior
categories:
- Runtime
- Production Sensors
see_also:
- SO-006
- SO-006c
- SO-006d
- change
last_reviewed: '2026-08-24'
references:
- title: The Tail at Scale
  year: 2013
  tier: III
  url: https://www.barroso.org/publications/TheTailAtScale.pdf
  kind: publication
  authors: Jeffrey Dean, Luiz André Barroso
  venue: Communications of the ACM 56(2)
- title: Dapper paper
  url: https://research.google/pubs/pub36356/
  kind: tool
- title: OpenTelemetry
  kind: tool
  url: https://opentelemetry.io
  description: Open-standard observability instrumentation
- title: Jaeger
  kind: tool
  url: https://www.jaegertracing.io
  description: Distributed tracing backend
- title: Zipkin
  kind: tool
  url: https://zipkin.io
  description: Distributed tracing system
- title: Tempo
  kind: tool
  url: https://grafana.com/oss/tempo
  description: Grafana-backed distributed tracing
---

What path did this particular operation take? A sensor of *execution flow*
across service boundaries — the span tree is itself a signal.

A trace shows you the actual path a request took through your system:
which services were called, in what order, how long each took. Where
[observability events](observability-events.html) give you per-execution
facts, traces give you the *shape* of execution.

## In practice

A typical reading is a trace waterfall for one slow request:

```
trace 4f2c9a (GET /checkout)  total 2.41s
api-gateway            |########################| 2410ms
  auth.verify          |#|                        84ms
  cart.fetch           |###|                     190ms
  payment.authorize    |#################|      1830ms
    stripe.call        |################|       1790ms
```

| Span | Duration | Share of trace |
|------|----------|----------------|
| payment.authorize | 1830 ms | 76% |
| stripe.call (child) | 1790 ms | 74% |
| cart.fetch | 190 ms | 8% |
| unaccounted gaps | 306 ms | 13% |

Reading it well:

- **Read the critical path, not the sum.** Parallel spans overlap; the
  trace total is the longest chain, and optimizing off-path spans buys
  nothing.
- **Mind the gaps.** Time between spans is uninstrumented work: queue
  waits, serialization, connection setup. A trace that sums to less than
  its total is pointing at what it cannot see.
- **One trace is an anecdote.** Pull many traces of the same endpoint and
  look for the span that is slow in most of them. The common span is the
  regression; the lone outlier is a story.
- **Shape is signal too.** A new child span means a new dependency, even
  when everything is fast. The graph changing is itself worth noticing.

## Response playbook

When a trace (or a set of traces) shows an operation over budget:

1. **Confirm the span is slow across traces, not in one.** Pull a batch of
   traces for the same endpoint and check how often the suspect span
   dominates. Slow in most traces is a regression; slow in one is a tail
   event worth a second look.
2. **Classify the span's time.** Is it compute, a downstream call, a lock
   wait, or a gap? The answer routes the fix:
   [continuous profiling](continuous-profiling.html) for compute,
   the downstream service's owner for calls, and the uninstrumented gap
   as its own investigation.
3. **Check for new spans and new depth.** A child span that did not exist
   last week is a new dependency, and each hop adds latency and failure
   modes. New shape on the critical path deserves a review even when the
   numbers look fine.
4. **Decide the containment.** If the slow span sits behind a deploy or
   a config change, revert or roll back rather than optimizing under
   pressure. If it is a long-standing problem, file it with the trace
   IDs as evidence and budget the fix.
5. **Add the missing span before closing.** If the slowest segment was an
   unaccounted gap, instrument it. Every incident resolved by guesswork
   is a span that should have existed.

## What it cannot detect

Traces show execution paths but not [correctness](runtime-invariants.html).
A trace that completes successfully may still violate a business invariant.
Pair traces with [invariant checking](runtime-invariants.html) for
correctness signal.
