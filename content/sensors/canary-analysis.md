---
id: SO-007
title: Canary Analysis
family: change
family_num: '07'
oracle: high
oracle_note: divergence on real traffic is strong evidence
independence: high
independence_note: production behavior cannot be gamed
scope: system
latency: minutes
actionability: guiding
actionability_note: shows which metrics diverged
type: retrospective
stack_level: canary-shadow
categories:
- Change
- Deployment Safety
see_also:
- SO-007b
- SO-007c
- SO-007d
- SO-005c
- SO-007e
last_reviewed: '2026-08-26'
references:
- title: Exploring Statistical Change Point Detection Techniques for Performance Anomaly Detection at Mozilla
  year: 2026
  tier: I
  url: https://arxiv.org/abs/2606.18377
  kind: publication
  authors: Mohamed Bilel Besbes, Gregory Mierzwinski, Suhaib Mujahid, Philipp Leitner, Alexander Serebrenik, Dave Hunt, Diego Elias Costa
  venue: arXiv preprint
- title: Holistic Configuration Management at Facebook
  year: 2015
  tier: III
  url: https://sigops.org/s/conferences/sosp/2015/current/2015-Monterey/printable/008-tang.pdf
  kind: publication
  authors: Chunqiang Tang, Thawan Kooburat, Pradeep Venkatachalam, Akshay Chander, Zhe Wen, Aravind Narayanan, Patrick Dowell, Robert Karl
  venue: SOSP '15
- title: Netflix Kayenta
  url: https://github.com/spinnaker/kayenta
  kind: tool
- title: Kayenta
  kind: tool
  url: https://github.com/spinnaker/kayenta
  description: Netflix's automated canary analysis
- title: Argo Rollouts
  kind: tool
  url: https://argoproj.github.io/rollouts
  description: Kubernetes progressive delivery
- title: Flagger
  kind: tool
  url: https://flagger.app
  description: Kubernetes progressive delivery and canary
---

Does the new version behave differently from the old version? A sensor of
*behavioral drift* between deployments, measured on real traffic.

Canary analysis routes a small percentage of production traffic to the new
version and compares its behavior to the old. If error rates, latency, or
[invariant violations](runtime-invariants.html) diverge, the canary fails.

## In practice

A canary reading is a side-by-side comparison of the same metric across two
populations, usually scored into a single pass/fail verdict rather than
eyeballed per metric:

| Metric | Baseline v2.40.7 | Canary v2.41.0 (5%) | Deviance | Tolerance | Verdict |
|--------|------------------|---------------------|----------|-----------|---------|
| Error rate | 0.12% | 0.84% | 7.0x | 2x | FAIL |
| p99 latency | 212 ms | 231 ms | +9% | +10% | pass |
| Success rate | 99.88% | 99.16% | -0.72 pp | -0.10 pp | FAIL |
| CPU | 0.41 cores | 0.43 cores | +5% | +20% | pass |
| **Overall score** | | | | | **42 / 100 — ROLLBACK** |

The tolerance column is the part that was decided before the canary ran.
Read the table without it and the verdicts look arbitrary: a 9% latency
bump passes and a 0.72-point drop in success rate fails, with nothing on
the page saying why. Read it with the column and every verdict is
arithmetic.

Reading it well requires four habits:

1. **Compare, don't threshold.** "Error rate 0.84%" means nothing on its
   own; the baseline at 0.12% is what makes it a signal. A canary judged
   against an absolute bar silently passes when everything degrades
   together.
2. **Set the tolerance before the canary runs.** Every metric needs a
   band written into the analysis config in advance. Note where that
   bites in the table above: latency came in at +9% against a +10%
   band and passed. Decided afterwards, +9% is whatever the person
   reading it needs it to be — a regression if they were suspicious, a
   Tuesday if they want to ship. Pre-set bands are also what stop the
   argument that a failing canary was "close enough."
3. **Know which metrics are allowed to move.** Latency within the noise
   band is normal churn. Error rate and invariant violations are not. If
   the score weights treat them alike, noise drowns the real divergences.
4. **Match the populations.** The canary and baseline must see comparable
   traffic. Comparing a canary that only handles new signups against a
   baseline serving the whole fleet reads drift into routing, and the
   "drift" is the routing.

The verdict is only as good as the metrics underneath it, which is why the
canary is downstream of the [observability work](observability-events.html)
rather than a replacement for it.

## What it cannot detect

Canary analysis can only detect differences in metrics you're measuring.
Unknown unknowns require [high-cardinality events](observability-events.html)
to investigate after the fact.
