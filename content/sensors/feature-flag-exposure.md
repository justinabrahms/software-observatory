---
id: SO-015
title: Feature Flag Exposure Telemetry
family: change
family_num: '07'
oracle: high
oracle_note: evaluation events are direct records of what each request saw
independence: high
independence_note: emitted by the flag infrastructure, not the feature code
scope: system
latency: seconds
actionability: guiding
actionability_note: tells you the true exposure of a change
type: retrospective
stack_level: production-behavior
categories:
- Change
- Production Sensors
see_also:
- SO-007
- SO-006c
- SO-012c
- SO-007e
last_reviewed: '2026-08-24'
references:
- title: Holistic Configuration Management at Facebook
  year: 2015
  tier: III
  url: https://sigops.org/s/conferences/sosp/2015/current/2015-Monterey/printable/008-tang.pdf
  kind: publication
  authors: Chunqiang Tang, Thawan Kooburat, Pradeep Venkatachalam, Akshay Chander, Zhe Wen, Aravind Narayanan, Patrick Dowell, Robert Karl
  venue: SOSP '15
- title: Development and Deployment at Facebook
  year: 2013
  tier: III
  url: https://www.cs.huji.ac.il/w~feit/papers/FB13IC.pdf
  kind: publication
  authors: Dror G. Feitelson, Eitan Frachtenberg, Kent L. Beck
  venue: IEEE Internet Computing 17(4)
- title: Feature flags
  url: https://martinfowler.com/articles/feature-toggles.html
  kind: tool
- title: LaunchDarkly
  kind: tool
  url: https://launchdarkly.com
  description: Feature management platform
- title: Statsig
  kind: tool
  url: https://www.statsig.com
  description: Experimentation and feature flag platform
- title: GrowthBook
  kind: tool
  url: https://www.growthbook.io
  description: Open-source feature flagging and A/B testing
- title: Unleash
  kind: tool
  url: https://www.getunleash.io
  description: Open-source feature flag management
---

A change behind a flag is not a change anyone has experienced. Flag
evaluation streams answer "who is actually seeing the new behavior, right
now?" — the difference between *deployed* and *live*, and the ground truth
underneath every [canary analysis](canary-analysis.html) claim about a
rollout's state.

## In practice

The core reading is an exposure matrix: which flags are evaluating true,
for whom, and how stale the flag itself is.

| Flag | State | Exposure | Target | Age | Coupling |
|------|-------|----------|--------|-----|----------|
| new-checkout-flow | ramping | 5% | 100% | 4 days | 0 flags |
| dark-mode-v2 | launched | 100% | n/a | 14 months | 0 flags |
| legacy-export-path | decaying | 100% | off | 26 months | 3 flags |
| exp-pricing-b | experimenting | 50% | n/a | 3 weeks | 0 flags |

Reading it well:

1. **Deployed is not live.** A flag at 0% exposure means nobody has seen
   the code, whatever the deploy dashboard says.
2. **Flags launched to 100% with no removal date are dead code with a
   gate.** They accumulate coupling and mask which path actually runs.
3. **Coupled flags are a compound condition.** When flag A only matters
   because flag B is on, you are testing one corner of a state space,
   not two features.
4. **Tie exposure to the verdict.** Exposure tells you the denominator;
   the [canary analysis](canary-analysis.html) tells you what happened to
   that population.

## How it gets gamed

- **Launch and walk away.** Flipping a flag to 100% counts as "done"
  while nobody removes the gate, so the codebase accrues dead branches
  that still count as live features in reporting.
- **Never delete the flag.** Old flags at 100% exposure pad feature
  counts and hide which paths real traffic uses; removal is the work
  that nobody schedules.
- **Ramp only in quiet hours.** Exposure telemetry read during a
  maintenance window shows a calm rollout that nothing real ever
  exercised.
- **Split flags to dodge review.** A feature gated by three coupled
  flags is harder to reason about and easier to slip past a reviewer
  than one flag at full exposure.

The meta-signal is the ratio of launched-but-unremoved flags to active
ramps.

## Response playbook

When the exposure matrix reads badly:

1. **Kill the stale flags.** Every flag launched to 100% more than a
   release cycle ago gets a removal task; delete the gate and the dead
   branch it guards.
2. **Map the coupled flags.** For any flag whose behavior depends on
   another flag, write down the actual state space and decide which
   combinations are tested. Untested corners are the incident waiting
   to happen.
3. **Put an expiry date on every new flag.** At creation time, record
   the target exposure and the removal date; telemetry makes both easy
   to audit.
4. **Reconcile exposure against reality.** Compare the matrix with
   [canary analysis](canary-analysis.html) verdicts; exposure without a
   behavioral verdict is a rollout nobody verified.

## What it cannot detect

Whether the new behavior is *correct* — only where it is *active*. Exposure
is the denominator; behavioral evidence still has to come from
[synthetic monitoring](synthetic-monitoring.html) or real traffic.
