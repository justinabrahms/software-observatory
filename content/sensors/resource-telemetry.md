---
id: SO-006d
title: Resource Telemetry
family: runtime
family_num: '06'
oracle: low
oracle_note: aggregate state, not causation
independence: high
independence_note: production reality
scope: system
latency: seconds
actionability: exploratory
actionability_note: but low dimensionality limits investigation
type: retrospective
stack_level: production-behavior
categories:
- Runtime
see_also:
- SO-006
- SO-006b
- SO-006c
last_reviewed: '2026-08-24'
references:
- title: Prometheus
  url: https://prometheus.io
  kind: tool
  description: Metrics collection and alerting
- title: Datadog
  kind: tool
  url: https://www.datadoghq.com
  description: Cloud monitoring and observability
- title: Grafana
  kind: tool
  url: https://grafana.com
  description: Metrics visualization and dashboards
- title: CloudWatch
  kind: tool
  url: https://aws.amazon.com/cloudwatch
  description: AWS monitoring and metrics
---

CPU, memory, IO, network, GC, queues. Traditional monitoring — useful but
limited. Low cardinality, low dimensionality, predetermined questions.

Resource telemetry is the weakest runtime sensor. It tells you aggregate
system state ("CPU is 82%") but not *which* requests or *which* code paths
caused it. [Observability events](observability-events.html) are a strictly
richer sensor — they preserve the per-request context that telemetry
discards.

## In practice

A typical reading is an alert firing against aggregate state:

```
[FIRING:1] CheckoutCPUHigh checkout prod us-east-1
  Summary: checkout CPU above 85% for 5m
  Value: 0.912
  Started: 2026-08-23 14:02 UTC
```

The alert names the resource, not the cause. The dashboard behind it
usually holds the first real comparison:

| Replica | CPU (5m avg) | Memory | p99 latency |
|---------|--------------|--------|-------------|
| checkout-1 | 0.91 | 1.8 GiB | 840 ms |
| checkout-2 | 0.42 | 1.2 GiB | 210 ms |
| checkout-3 | 0.44 | 1.2 GiB | 195 ms |

Reading it well:

- **Distrust averages.** The fleet mean is 0.59, under threshold, while
  one replica is pinned. Alert and read on distributions or per-replica
  values, not on the mean.
- **Overlay change and traffic.** A CPU rise that starts at a deploy
  boundary is code; one that tracks request volume is capacity. Same
  number, different answer.
- **Treat telemetry as a doorway, not a diagnosis.** Aggregate state says
  something is wrong somewhere. The next step is a richer sensor:
  [continuous profiling](continuous-profiling.html) for where the CPU
  goes, [distributed traces](distributed-traces.html) for which requests
  suffer.

## How it gets gamed

Telemetry is collected by machines, but it is curated and answered by
people:

- **Alert fatigue as suppression.** Pages get muted "for now," thresholds
  get raised after each alert, until the metric that would have caught
  the incident quietly stops calling anyone. Rising thresholds without
  a matching fall in incidents is the tell.
- **Averaging out the victims.** Reporting fleet means while one replica
  or one region burns. The dashboard says healthy; the users on the hot
  replica disagree.
- **Buying capacity instead of finding cause.** Scaling up resets the
  gauge and closes the ticket, so the underlying leak never gets a
  diagnosis. The sensor keeps reading normal because the budget grew,
  not because the problem left.

The meta-signal is the ratio of muted or raised alerts to active ones.
A sensor nobody gets paged by is a sensor nobody is running.

## Response playbook

When a resource alert fires:

1. **Verify before escalating.** Check that the reading is real and
   persistent: confirm per-replica values, not just the aggregate, and
   rule out a monitoring-agent or clock skew artifact.
2. **Overlay change and traffic.** Put the deploy timeline and request
   volume over the same window. A step at a deploy points at code; a
   climb with traffic points at capacity. The answer decides the next
   move.
3. **Contain first.** Shed load, restart the hot replica, or scale the
   pool to stop user impact. Containment is not the fix; it is what
   buys time for the diagnosis.
4. **Trace the resource to a request.** Telemetry cannot say which code
   path is burning, so hand off immediately:
   [continuous profiling](continuous-profiling.html) for where the
   CPU goes, [distributed traces](distributed-traces.html) for which
   requests suffer.
5. **File the follow-up before closing.** If the cause was a leak or a
   regression, open the ticket that adds the missing alert or limit
   while the incident is still fresh.

## What it cannot detect

Resource telemetry cannot tell you *why* resources are consumed or *which*
requests are responsible. It shows aggregate state, not per-execution
reality. This is why [observability events](observability-events.html) are a
strictly richer sensor.
