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

Real user monitoring (RUM) measures what happens when people use your
application: how long content takes to appear, how quickly a page responds,
and which actions fail. Their devices and networks supply conditions you
probably did not think to put in a test plan.

A successful server response can still leave someone staring at a frozen
checkout button. RUM collects measurements in the client, where that delay
is visible. [Synthetic monitoring](synthetic-monitoring.html) runs the
journeys you script; RUM observes the ones people actually take. It is a
client-side form of [observability](observability-events.html), and its
usefulness depends on who makes it into the data.

## What to measure

Start with something a person can notice. Google's Core Web Vitals cover
three aspects of a web page's performance:

- **Largest Contentful Paint (LCP):** when the largest eligible piece of
  content in the visible area appears. This helps answer whether the page
  still looks as though it is loading.
- **Interaction to Next Paint (INP):** how quickly the page responds
  visually to qualifying interactions, such as clicks, taps, and key
  presses, over a visit.
- **Cumulative Layout Shift (CLS):** how much visible content moves
  unexpectedly. Think of a button scooting away just as you try to click it.

INP replaced First Input Delay (FID) as a Core Web Vital in March 2024.
If your dashboard still uses FID for that assessment, update it.

Google's October 2024 guidance evaluates these at the **75th percentile**,
separately for mobile and desktop. That is the value at or below which
75% of observations fall, often written as p75. Its “good” thresholds are
at most 2.5 seconds for LCP, 200 milliseconds for INP, and 0.1 for CLS.
These are useful starting points for a performance budget. They do not tell
you whether a page displayed the right price.

The `web-vitals` library handles the measurement and reporting details.
Keep the observation count for each metric: a visit without a qualifying
interaction has no INP reading. Ten thousand sessions do not necessarily
mean ten thousand measurements of everything.

Also collect client errors and outcomes for actions you care about, such
as completing checkout. Handled failures need explicit reporting; an API
request can fail, show an error message, and never produce an uncaught
exception. Browser timing APIs can help separate time spent fetching assets
from time spent waiting for API responses, although cross-origin timing
detail may be restricted.

Define what each rate counts. One session with twenty exceptions is one
affected session, but twenty errors. A checkout failure rate also needs a
definition of an attempt, including what happens when someone abandons it.
Write those definitions down where the next person reading the chart can
find them.

## Reading a release

Here is an illustrative comparison of one checkout route over equal time
windows. The error percentages count sessions with at least one client
error; p75 means the 75th percentile.

| Release and device | Observed sessions | Sessions with client errors | LCP p75 | INP p75 |
|--------------------|------------------:|---------------------------:|--------:|--------:|
| Previous, mobile | 10,000 | 100 (1%) | 2.2 s | 180 ms |
| Current, mobile | 10,000 | 600 (6%) | 3.4 s | 310 ms |
| Previous, desktop | 10,000 | 100 (1%) | 1.4 s | 110 ms |
| Current, desktop | 10,000 | 100 (1%) | 1.4 s | 110 ms |

The mobile rows give you a place to start: more sessions have errors, and
both performance measures have worsened. The desktop readings are unchanged.
An overall average could make this much less obvious.

The table does not establish that the release caused the change. Browser
versions, network conditions, or collection settings could have shifted
between the windows. Check those before attributing the regression to the
new code. The session counts let you check the error rates; you still need
the eligible observation counts to assess the performance percentiles.

Keep the release, route template, browser, device class, and sampling rate
with the readings. A route template such as `/orders/:id` lets you group
requests without collecting every order identifier. Where possible, use a
scoped correlation identifier to connect a client failure to a
[distributed trace](distributed-traces.html). You should be able to
investigate a slow page without collecting raw form fields, query strings,
or persistent personal identifiers.

## In practice

Start with a few journeys someone will act on: signing in, opening a busy
screen, completing checkout. Decide which outcomes to report and set
performance limits per device class before looking at a release's results.
That makes it harder to explain away a mobile regression because desktop
still looks fine.

Put the readings next to the release that produced them, and agree who
will review them. A weekly review can catch gradual drift; a breached
release limit needs attention when it happens. Keep browser, application,
and instrumentation versions so you can investigate which change affected
the measurement.

Collect enough detail to make that investigation possible. Remove fields
that nobody uses: each one needs maintaining and may collect information
you did not need. If a measured journey never prompts a decision, ask
whether it needs different measurements or whether you can stop collecting
it.

## How it gets gamed

It is possible to improve the chart without improving the application:

- **Drop the awkward traffic.** Removing a slow route or device class
  makes the aggregate look healthier. Record coverage changes and compare
  the same groups across releases.
- **Change the counting.** Keeping every error while sampling only a small
  fraction of successful sessions inflates an unadjusted error rate.
  Changing that sampling later can look like a fix. Retain observation
  counts and sampling probabilities so rates can be compared consistently
  or weighted for unequal sampling.
- **Rename the failure.** Catching an exception may improve error handling,
  but it does not necessarily make the action succeed. Keep reporting the
  outcome when a failure becomes handled.
- **Quietly change the filters.** Removing bots or synthetic checks may be
  a sensible correction. Presenting the resulting drop in latency as a
  product improvement is misleading. Annotate the filter change.

Compare incidents with what RUM reported. If users struggled and the
readings stayed healthy, check which users, routes, and failures were
represented before trusting the next green chart.

## Response playbook

First check the measurement. Did collection volume, bot filtering, sampling,
or eligibility for a metric change? Then compare users on the same route,
device class, and browser over comparable windows. Treat small samples
cautiously. Percentiles from separate groups cannot simply be averaged
together to recover the combined percentile.

Inspect a few representative failures using error stacks with sensitive
data removed, timing details, and trace links. Look for where the delay or
failure occurs: rendering, the network, a third-party script, or your API.
Use the failure budget or performance limit agreed before the release to
decide whether to roll back or disable a feature.
[Canary analysis](canary-analysis.html) can use these readings too.

After the fix, check the affected group again. A passing lab test helps
explain why the fix should work. Recovery in the field tells you whether
it helped those users. Check that they are still reporting before declaring
the problem resolved.

## What it cannot detect

RUM only sees clients that report. Script blockers, consent choices, early
exits, crashes, and a broken collection endpoint can leave visits missing.
Compare collection volume with an independent source and investigate sudden
drops. That comparison can reveal missing reports; it cannot reconstruct
the experience of every missing client.

The reports you do receive may include automation. Bots that execute
JavaScript and your own synthetic checks can contribute timings and errors.
Label known automation and inspect it separately. User-agent filtering only
catches bots that identify themselves; the remaining traffic is not
guaranteed to be human.

Measurements can also change when browsers or instrumentation change.
Keep their versions and check the
[Web Vitals changelog](https://chromium.googlesource.com/chromium/src/+/main/docs/speed/metrics_changelog/README.md)
when a shift has no apparent application cause.

RUM cannot tell you about people who never arrive or paths nobody visits.
It also cannot prove accessibility or establish that a completed purchase
had the correct price from performance readings alone. Use synthetics for
scripted paths when traffic is quiet, business invariants for correct
outcomes, and [load testing](load-testing.html) for controlled stress.
