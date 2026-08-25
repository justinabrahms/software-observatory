---
id: SO-015b
title: DORA Metrics
family: evolution
family_num: 09
oracle: medium
oracle_note: the metrics proxy safety; they are not safety
independence: high
independence_note: derived from deployment and incident records, not self-report
scope: system
latency: days
actionability: guiding
actionability_note: tells you which stage of the pipeline to distrust
type: retrospective
stack_level: canary-shadow
categories:
- Evolution
see_also:
- SO-009
- SO-009b
- SO-009d
last_reviewed: '2026-08-24'
references:
- title: 'Accelerate: State of DevOps 2019'
  year: 2019
  tier: II
  url: https://dora.dev/research/2019/dora-report/2019-dora-accelerate-state-of-devops-report.pdf
  kind: publication
  authors: Nicole Forsgren, Dustin Smith, Jez Humble, Jessie Frazelle
  venue: DORA / Google Cloud
- title: 2017 State of DevOps Report
  year: 2017
  tier: II
  url: https://dora.dev/research/2017/2017-state-of-devops-report.pdf
  kind: publication
  authors: Nicole Forsgren, Jez Humble, Gene Kim, Alanna Brown, Nigel Kersten
  venue: Puppet + DORA
- title: DORA
  url: https://dora.dev
  kind: tool
- authors: Forsgren et al.
  title: Accelerate
  year: 2018
  kind: publication
  tier: I
- title: DORA survey
  kind: tool
  url: https://dora.dev
  description: DORA research assessment survey
- title: DevOps Research Assessment
  kind: tool
  url: https://dora.dev/research/
  description: DORA's four-metric assessment tool
scope_note: organization-level delivery performance
---

Deployment frequency, lead time for changes, change failure rate,
reliability, time to restore. Five numbers about how changes have
historically flowed through this organization — a sensor of delivery
*pattern*, answering "does our recent past look like teams that ship
safely?" Reliability was added in DORA 2023 as the fifth metric, reflecting
that stability is measured by whether the system meets its reliability
targets, not just by how fast failures are fixed.

## In practice

The reading is a dashboard of the five numbers over a trailing window,
compared against the team's own history rather than an industry table:

| Metric | Last quarter | This quarter | Trend |
|--------|--------------|--------------|-------|
| Deploy frequency | 14 / week | 6 / week | down |
| Lead time for changes | 36 hours | 61 hours | up (worse) |
| Change failure rate | 4% | 11% | up (worse) |
| Time to restore | 45 minutes | 3 hours | up (worse) |
| Reliability target met | yes | no | worse |

Reading it well:

1. **Read the five together.** Deployment frequency falling alone might
   be a deliberate pause; falling alongside rising failure rate and
   lead time is a pipeline in trouble. One number is an anecdote, five
   are a pattern.
2. **Compare against the team's own baseline.** Industry quartiles
   tell you what other teams do, not what changed here. The trend line
   is the signal.
3. **Distrust flat perfection.** Metrics that never move usually mean
   the instrumentation is stale or the definitions quietly widened.
4. **Follow a bad number to its records.** The dashboard locates the
   quarter; the deploy log and incident timeline explain it.

## How it gets gamed

DORA metrics are classically gameable, because every one of them can be
moved without moving the underlying delivery health:

- **Batch deploys to inflate frequency.** Shipping twenty small commits
  as one "deploy" or splitting one change into ten trivial ones; the
  frequency number moves either way, depending on which direction
  flatters the dashboard.
- **Cherry-pick easy deploys.** Counting only the low-risk service
  whose pipeline is mature, while the painful path everyone actually
  uses goes unmeasured.
- **Close incidents early.** Marking an incident resolved when the page
  stops, not when users are unaffected, buys time-to-restore without
  restoring anything.
- **Redefine failure downward.** If only rollbacks count as failures,
  teams hotfix forward and the change failure rate falls by definition.
- **Tighten the reliability denominator.** Meeting a target is easy
  when the target was quietly negotiated down after the quarter
  started.

The meta-signal is definitional drift: log the metric definitions and
the counting rules alongside the numbers, and treat any unannounced
change to them as a finding in itself.

## Response playbook

When the dashboard degrades:

1. **Verify the definitions first.** Before acting, confirm the numbers
   were computed the same way as last quarter. Half of all "sudden"
   DORA regressions are a pipeline or counting change, not a delivery
   change.
2. **Trace the lead-time increase stage by stage.** Split lead time
   into review, build, test, and deploy waits; the longest stage is
   the one to attack, and it is almost never the one people guess.
3. **Correlate failure rate with incident records.** Use [incident
   correlation](incident-correlation.html) to see whether failures are
   clustering in one service or one change type before prescribing a
   fix.
4. **Lower batch size, not ambition.** If deploys are failing more,
   ship smaller changes with [canary analysis](canary-analysis.html)
   in front of them; do not add another approval gate, which raises
   lead time and failure rate together.
5. **Re-measure after one quarter.** The dashboard lags; give any fix a
   full window before judging it, and say so when the numbers are
   reported.

## What it cannot detect

The cause of a bad number. DORA metrics locate the problem in time and
stage; understanding it requires [decision provenance](decision-provenance.html)
and [incident correlation](incident-correlation.html). And like all metrics
that become targets, they invite gaming — deployment frequency can be raised
by shipping trivia.
