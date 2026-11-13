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
- title: Web Vitals (October 2024 revision)
  authors: Philip Walton
  year: 2024
  kind: blog
  url: https://web.dev/articles/vitals
- title: Interaction to Next Paint becomes a Core Web Vital on March 12
  authors: Jeremy Wagner, Rick Viscomi
  year: 2024
  kind: blog
  url: https://web.dev/blog/inp-cwv-march-12
- title: Web Vitals Changelogs
  kind: other
  url: https://chromium.googlesource.com/chromium/src/+/main/docs/speed/metrics_changelog/README.md
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
- title: Identify Bots in the RUM Explorer
  kind: other
  url: https://docs.datadoghq.com/real_user_monitoring/guide/identify-bots-in-the-ui/
---

Real user monitoring (RUM) measures how an application performs for people
using it: how long pages take to load, how quickly they respond, and where
users encounter errors. It captures devices, networks, and interactions
that a test lab can miss.

A server can return a successful response while the browser spends seconds
blocked on JavaScript or fails to display the result. RUM helps close that
gap. Where [synthetic monitoring](synthetic-monitoring.html) runs a scripted
journey, RUM follows the journeys people actually take. It is a client-side
form of [observability](observability-events.html), with the same need to
ask whether the data represents the people you meant to observe.

## What to measure

Start with what a person can notice. Google's Core Web Vitals describe
three parts of the experience: **Largest Contentful Paint (LCP)** measures
when the largest eligible piece of visible content appears;
**Interaction to Next Paint (INP)** measures responsiveness to qualifying
interactions during a visit; **Cumulative Layout Shift (CLS)** measures
unexpected movement of visible content. A page can do well on all three
and still display the wrong price.

INP replaced First Input Delay (FID) as a Core Web Vital in March 2024.
A dashboard that still reports FID needs updating to assess the current set.

Google's Web Vitals guidance, updated in October 2024, calls for evaluating
these at the **75th percentile**, separately for mobile and desktop. That is
the value at or below which
75% of the observations fall. Good values are at most 2.5 seconds for LCP,
200 milliseconds for INP, and 0.1 for CLS. The `web-vitals` library handles
the details of measuring and reporting them. A visit without a qualifying
interaction has no INP reading, so keep the observation count for each
metric rather than assuming every session contributed one.

Performance is only part of the picture. Collect client errors and the
outcomes of important actions, such as completing checkout. Browser timing
APIs can help show whether a delay came from fetching an asset or waiting
for an API response, though cross-origin timing detail may be restricted.
A fast response still needs a check that it contained the right result.

Be explicit about what a rate counts. “Errors per request” and “sessions
with an error” answer different questions: one session with twenty
exceptions is still one affected session. Likewise, a checkout failure
rate needs a definition of an attempt, including how abandoned attempts
are counted. Handled failures need their own reporting; uncaught exceptions
alone will miss them.

## Reading a release

These illustrative readings compare one checkout route over equal time
windows. Here, p75 means the 75th percentile:

| Release and device | Observed sessions | Sessions with client errors | LCP p75 | INP p75 |
|--------------------|------------------:|---------------------------:|--------:|--------:|
| Previous, mobile | 10,000 | 100 (1%) | 2.2 s | 180 ms |
| Current, mobile | 10,000 | 600 (6%) | 3.4 s | 310 ms |
| Previous, desktop | 10,000 | 100 (1%) | 1.4 s | 110 ms |
| Current, desktop | 10,000 | 100 (1%) | 1.4 s | 110 ms |

Mobile users are seeing more errors and slower responses while desktop
users are seeing little change. That gives the investigation a place to
start. It does not yet establish that the release caused the regression:
the browser versions, network conditions, or collection settings may also
have changed. The session counts support the error rates; interpreting
the percentiles also requires the counts of eligible metric observations.

Keep enough context to follow that lead: the release, route template,
browser, device class, and sampling rate. Where possible, use a scoped
correlation identifier to connect a client failure to a
[distributed trace](distributed-traces.html). Raw form fields, query
strings, and persistent personal identifiers should not be the price of
being able to investigate a slow page.

## In practice

Running this is a weekly rhythm, not a dashboard someone remembers to open.

Pick the few journeys that matter — sign-in, the expensive screen, the checkout
step — and tag them as the measured set rather than collecting everything the
agent can emit. Decide the target before looking at the data: a percentile
budget per device class, so a mobile regression cannot hide inside a desktop
average. Keep the browser and build version on every reading, so a shift can be
attributed to a release or ruled out.

Then put the reading in front of the people who change code, next to the release
they shipped, and give someone the job of opening it once a week. A number with
no owner is a chart; a number with an owner and a threshold is a signal. When the
budget is crossed, the response playbook below says what to do; when nothing has
moved, the boring answer is the correct one and worth writing down.

Retire what stops earning its place. Every field collected is a privacy cost and
a maintenance cost, and a journey nobody acts on is instrumentation that will be
wrong before it is deleted.

## How it gets gamed

A dashboard can improve because its audience changed. Bots that execute
JavaScript can enter browser RUM data, as can your own synthetic checks.
Their timings, errors, and repeated journeys can distort the picture of
human experience. Label known automation and inspect it separately from
human traffic. Bot detection is imperfect: a user-agent filter catches
self-declared bots, not every automated browser. Record filter changes so
removing traffic cannot quietly pass for a performance improvement.

The opposite problem is losing the people with the worst experience.
Script blockers, consent choices, early exits, crashes, or a failed
collection endpoint can leave sessions unreported. Compare collection
volume with an independent source and investigate sudden drops. A client
that went silent has not demonstrated a successful visit.

Even the sessions you retain can mislead. A fast majority can hide a slow
device class in an overall average. Keeping every error but only a small
sample of successful sessions inflates a naive error rate. Compare the same
groups, retain observation counts, and record each session's chance of
being sampled so the rates can be calculated consistently or weighted to
account for unequal sampling.

Finally, the definition itself can move. Dropping a slow route, changing
metric versions, or reclassifying an error as handled can make the chart
look healthier without changing anyone's experience. Annotate those
changes alongside application releases. Browser updates can change the
measurement too; keep browser and instrumentation versions with the data,
and consult the [Web Vitals changelog](https://chromium.googlesource.com/chromium/src/+/main/docs/speed/metrics_changelog/README.md)
when readings shift without an application change.

## Response playbook

First check whether the reading is trustworthy. Did collection volume,
bot filtering, sampling, or metric eligibility change? Then narrow the
problem to a comparable group of users: the same route, device, browser,
and time window across releases. Small samples need caution, and
percentiles from separate groups cannot simply be averaged together.

Inspect a few representative failures using sanitized error stacks,
performance attribution, and trace links. Look for the point where the
experience breaks: rendering, the network, a third-party script, or the
API. Use a previously agreed failure budget or performance limit to decide
whether to roll back or disable a feature.
[Canary analysis](canary-analysis.html) can use these RUM readings too.

After the fix, check the affected users again. A passing lab run helps
explain the repair; recovery in the field shows whether it reached the
people who were struggling. Confirm that the readings recovered without
those people disappearing from the measured population.

## What it cannot detect

RUM cannot observe users who never arrive or clients that never report.
It cannot cover unvisited paths, prove accessibility, or establish that a
completed purchase had the correct price. Use synthetics to check scripted
paths even when traffic is quiet, business invariants to check correct
outcomes, and [load testing](load-testing.html) to apply controlled stress.
