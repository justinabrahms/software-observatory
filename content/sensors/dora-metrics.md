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
- title: A history of DORA's software delivery metrics
  url: https://dora.dev/insights/dora-metrics-history/
  kind: other
- title: DORA
  url: https://dora.dev
  kind: tool
- authors: Forsgren et al.
  title: Accelerate
  year: 2018
  kind: publication
  tier: I
- title: DevOps Research Assessment
  kind: tool
  url: https://dora.dev/research/
  description: DORA's research assessment tool
scope_note: organization-level delivery performance
---

Change lead time, deployment frequency, failed deployment recovery time,
change fail rate, deployment rework rate. Five numbers about how changes
have historically flowed through this organization — a sensor of delivery
*pattern*, answering "does our recent past look like teams that ship
safely?" This entry describes the five-metric model DORA has published
since 2024: the first three grouped as throughput, the last two as
instability.

The set is versioned, and the names move. "Time to restore service" was
renamed *failed deployment recovery time* in 2023, narrowing it to failures
a deployment caused rather than any outage; *deployment rework rate* arrived
in 2024 as the actual fifth metric. Reliability was added in 2021 and is not
one of the five — DORA's own history records that the report calling it "the
fifth metric" was inaccurate, and files it under operational rather than
delivery performance. A dashboard labelled "the DORA metrics" is dated by
which names it uses, and comparing readings across a rename compares two
sensors.

## In practice

The reading is a dashboard of the five numbers over a trailing window,
compared against the team's own history rather than an industry table:

| Metric | Last quarter | This quarter | Trend |
|--------|--------------|--------------|-------|
| Change lead time | 36 hours | 61 hours | up (worse) |
| Deployment frequency | 14 / week | 6 / week | down |
| Failed deployment recovery time | 45 minutes | 3 hours | up (worse) |
| Change fail rate | 4% | 11% | up (worse) |
| Deployment rework rate | 6% | 14% | up (worse) |

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
  stops, not when users are unaffected, buys recovery time without
  restoring anything.
- **Redefine failure downward.** If only rollbacks count as failures,
  teams hotfix forward and the change failure rate falls by definition.
- **File rework as planned work.** Deployment rework rate counts the
  deployments that exist only to fix something already shipped. Attach
  the hotfix to the next feature ticket and it stops counting, while
  the rework goes on happening.

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
