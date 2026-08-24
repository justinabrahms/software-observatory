---
id: SO-012c
title: Synthetic Monitoring
family: behavioral
family_num: '02'
oracle: high
oracle_note: a failed checkout flow is unambiguous
independence: high
independence_note: runs outside the system, against its public surface
scope: user-journey
latency: minutes
actionability: guiding
actionability_note: the failing step localizes the breakage
type: retrospective
stack_level: production-behavior
categories:
- Behavioral
- Production Sensors
see_also:
- SO-006c
- SO-007
- SO-012b
last_reviewed: '2026-08-24'
references:
- title: Meaningful Availability
  year: 2020
  tier: III
  url: https://www.usenix.org/system/files/nsdi20-paper-hauer.pdf
  kind: paper
  authors: Tamás Hauer, Philipp Hoffmann, John Lunney, Dan Ardelean, Amer Diwan
  venue: USENIX NSDI '20
- title: Monitoring Distributed Systems (SRE Book, ch. 6)
  year: 2016
  tier: IV
  url: https://sre.google/sre-book/monitoring-distributed-systems/
  kind: paper
  authors: Rob Ewaschuk, Betsy Beyer
  venue: Site Reliability Engineering, O'Reilly
- title: Checkly
  url: https://checklyhq.com
  kind: tool
  description: Synthetic monitoring as code
- title: k6
  kind: tool
  url: https://k6.io
  description: Open-source load testing tool
- title: Pingdom
  kind: tool
  url: https://www.pingdom.com
  description: Uptime and performance monitoring
- title: Datadog Synthetic
  kind: tool
  url: https://docs.datadoghq.com/synthetics/
  description: Synthetic monitoring in Datadog
scope_note: scripted end-to-end user flows
---

Scripted user flows run against the production system around the clock:
log in, search, add to cart, check out. Synthetic monitoring is a behavioral
test suite whose environment is the real world, giving you a baseline answer
to "does it do what we expect?" even when no user happens to be asking.

## In practice

A typical reading is a failed check, step by step:

```
CHECK checkout-flow FAILED  run 14:35 UTC  vantage fra-1
  step 1  GET  /login            200   312ms  ok
  step 2  POST /login            200   428ms  ok
  step 3  GET  /search?q=kettle  200   391ms  ok
  step 4  POST /cart             500  2104ms  FAILED
  step 5  POST /checkout         ---  skipped
```

| Vantage | Result | Failing step | p95 latency |
|---------|--------|--------------|-------------|
| fra-1 | FAIL | POST /cart (500) | 2104 ms |
| iad-1 | FAIL | POST /cart (500) | 1980 ms |
| sin-1 | PASS | | 412 ms |

Reading it well:

- **Read the step, not the check name.** "checkout-flow failed" is a
  headline; "step 4, POST /cart, 500" is a lead. The failing step is the
  localization the sensor exists to give.
- **One failure is a question, three is a signal.** Checks hit real
  infrastructure and flake. Confirmation avoids paging on a blip, but
  retries tuned high enough to always pass have silenced the sensor.
- **Separate target failure from probe failure.** Expired test
  credentials, a blocked agent IP, and a stale selector all look like
  the system failing. The error body usually says which.
- **Suspect a check that always passes.** Assertions weaken over time; a
  five-year-old check that has never failed may no longer be checking
  anything.

## How it gets gamed

Synthetics are owned by the teams that ship the flows, so they can be
tuned to pass:

- **Checks tuned to green.** Slow assertions get wider timeouts, flaky
  steps get more retries, and the check that used to fail in 2 seconds
  now passes in 40. The monitor still "works"; it just stopped sensing.
- **Silence as maintenance.** A failing check gets snoozed "until the
  deploy lands," then the snooze gets extended, then forgotten. Muted
  checks are the sensor's off switch.
- **Testing the happy path only.** Checks that avoid the paths where bugs
  live, or that run only from the best-connected region, report a green
  board over a real degradation elsewhere.
- **Credential theater.** Expired test credentials make the check fail
  for reasons that have nothing to do with the system; after a while
  everyone learns to ignore check failures, real or not.

The meta-signal is the check pass rate over months. A fleet of checks
that has not failed in a year, on a system that has had incidents in the
same year, is a sensor that has been tuned silent.

## Response playbook

When a synthetic check fails:

1. **Confirm the failure.** Re-run the check, or wait for the next
   scheduled run if it is minutes away. One failure is a question; two
   consecutive failures are a signal. Do not page on a single blip, and
   do not tune the retry count high enough to make this step meaningless.
2. **Rule out the probe.** Check whether the failure is in the target or
   in the test itself: expired credentials, blocked agent IPs, a stale
   selector, a provider outage at the vantage point. The failing step's
   error body usually says which.
3. **Measure the blast radius.** Check the same flow from other vantage
   points and check real-user metrics for the same endpoint. If only one
   region fails, suspect network or regional infrastructure; if all fail,
   suspect the service.
4. **Correlate with recent changes.** Overlay the failure time with
   deploys and config changes. A check that fails within minutes of a
   deploy is a [canary](canary-analysis.html) that caught something, and
   the deploy owner is the next person to talk to.
5. **Keep the check armed after the fix.** Do not mute the check while
   investigating; that is how suppression starts. If the check is truly
   broken, fix the check in the same PR as the incident, and record why.

## What it cannot detect

Behavior outside the scripted paths. Synthetics cover the flows you thought
to script; the long tail of user behavior is the domain of
[observability events](observability-events.html) and real-user monitoring.
