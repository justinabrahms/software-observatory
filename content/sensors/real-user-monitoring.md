---
id: SO-006f
title: Real User Monitoring (RUM)
family: runtime
family_num: '06'
oracle: medium
oracle_note: measures experienced performance and failures; correctness needs an explicit outcome or threshold
independence: high
independence_note: actual devices and networks supply the workload, but the application team chooses instrumentation and sampling
scope: user-journey
latency: seconds
actionability: exploratory
actionability_note: segment by release, route, browser, and device to locate the affected population
type: retrospective
stack_level: production-behavior
categories:
- Runtime
- Production Sensors
see_also:
- SO-006
- SO-006b
- SO-006e
- SO-012c
- SO-007
references:
- title: Web Vitals
  authors: Philip Walton
  year: 2020
  kind: blog
  url: https://web.dev/articles/vitals
- title: Performance Timeline
  kind: spec
  url: https://www.w3.org/TR/performance-timeline/
- title: Resource Timing
  kind: spec
  url: https://www.w3.org/TR/resource-timing/
- title: web-vitals
  kind: tool
  url: https://github.com/GoogleChrome/web-vitals
  description: Browser library for measuring Core Web Vitals, with attribution builds for diagnosis
---

Real user monitoring (RUM) asks: *what experience did people actually have
in the client?* It collects performance and failure signals from real
sessions, including devices, networks, and interactions absent from a test lab.

A server can return every response successfully while a browser spends
seconds blocked on JavaScript or fails to render the result. RUM observes
that client boundary. [Synthetic monitoring](synthetic-monitoring.html)
exercises scripted journeys on chosen devices; RUM observes the journeys
people take. [Observability events](observability-events.html) supply the
broader event model; RUM gives it a client-side vantage point.

## What to measure

| Signal | Reading | Limit |
|--------|---------|-------|
| Largest Contentful Paint (LCP) | When the largest eligible visible content renders | Does not say the page is usable or correct |
| Interaction to Next Paint (INP) | Responsiveness across qualifying interactions during a page visit | Visits without qualifying interactions have no INP reading |
| Cumulative Layout Shift (CLS) | Unexpected movement of visible content | Stable content can still be wrong |
| Client errors | Sessions with uncaught exceptions or unhandled promise rejections, divided by observed sessions | Handled failures and missing telemetry need separate checks |
| Resource and request timings | Time spent fetching assets and API responses from the client | Cross-origin detail may be restricted; a fast request can return wrong data |
| Journey outcomes | Completed, failed, and abandoned attempts at a named action | Requires explicit definitions and a reliable attempt denominator |

Google's Web Vitals guidance evaluates LCP, INP, and CLS at the 75th
percentile, separately for mobile and desktop: good values are at most
2.5 seconds, 200 milliseconds, and 0.1 respectively. These are experience
thresholds, not proof of functional correctness. The browser Performance
Timeline and Resource Timing APIs provide timing records; the `web-vitals`
library handles metric lifecycles and reporting details.

For every rate, name the unit: errors per request, affected sessions per
session, or failed attempts per attempt. They answer different questions.
A session with twenty exceptions is still one affected session.

## Reading a release

Illustrative readings for one checkout route, over equal observation windows:

| Release and device | Observed sessions | Sessions with client errors | LCP p75 | INP p75 |
|--------------------|------------------:|---------------------------:|--------:|--------:|
| Previous, mobile | 10,000 | 100 (1%) | 2.2 s | 180 ms |
| Current, mobile | 10,000 | 600 (6%) | 3.4 s | 310 ms |
| Previous, desktop | 10,000 | 100 (1%) | 1.4 s | 110 ms |
| Current, desktop | 10,000 | 100 (1%) | 1.4 s | 110 ms |

The mobile cohort regressed in both responsiveness and client errors while
desktop stayed steady. That localizes investigation; it does not establish
that the release caused the change. Compare browser versions, network mix,
and instrumentation before treating the association as a verdict. The
percentiles describe eligible metric observations, whose counts should also
be recorded; they are not necessarily the session counts in the table.

Keep route templates, release identifiers, browser and device classes, and
sampling probabilities with the readings. Pair client failures with
[distributed traces](distributed-traces.html) using a scoped correlation
identifier where available. Avoid collecting raw form fields, query strings,
or persistent personal identifiers merely to make a chart easier to slice.

## How it gets gamed

- **Averages hide the victims.** A fast majority can conceal a slow device
  class. Keep percentiles and affected-session rates by meaningful cohort,
  along with observation counts.
- **The broken client goes silent.** Script blockers, consent choices,
  early navigation, crashes, and a failed telemetry endpoint can remove
  sessions from the denominator. Track collection health and compare
  counts with an independent source; silence is not a successful session.
- **Sampling changes the story.** Retaining every error but only a fraction
  of successful sessions biases a naive error rate. Preserve inclusion
  probabilities and use a consistent population or appropriate weighting.
- **The definition moves.** Renaming an error as handled, dropping a slow
  route, or changing metric versions can improve a dashboard without
  improving anyone's experience. Annotate instrumentation changes alongside
  application releases.

## Response playbook

1. **Check the sensor.** Verify event volume, metric eligibility, sampling,
   and collection failures before interpreting a sudden improvement or drop.
2. **Pin the affected cohort.** Compare the same route, device, browser,
   and time window across releases; retain counts and uncertainty for small
   samples. Do not average precomputed percentiles across cohorts.
3. **Inspect representative failures.** Use sanitized error stacks,
   performance attribution, and trace correlations to distinguish rendering,
   network, third-party, and API failures.
4. **Contain against an agreed boundary.** Use a journey failure budget or
   performance guardrail to decide whether to roll back or disable a feature.
   [Canary analysis](canary-analysis.html) can use RUM readings as inputs.
5. **Verify recovery in the affected clients.** A passing lab run is useful
   reproduction evidence; confirm that field readings recover and that the
   telemetry population did not shrink.

## What it cannot detect

RUM cannot observe users who never arrive or clients that never report. It
does not cover unvisited paths, prove accessibility, or establish that a
completed purchase had the correct price. Pair it with synthetics for quiet
periods and scripted paths, explicit business invariants for correct
outcomes, and [load testing](load-testing.html) for controlled stress.
