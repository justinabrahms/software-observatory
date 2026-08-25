---
id: SO-007b
title: Shadow Traffic
family: change
family_num: '07'
oracle: high
oracle_note: divergence on real inputs is strong evidence
independence: high
independence_note: production inputs
scope: system
latency: minutes
actionability: guiding
actionability_note: shows divergent requests and responses
type: retrospective
stack_level: canary-shadow
categories:
- Change
- Deployment Safety
see_also:
- SO-007
- SO-007c
- SO-005c
last_reviewed: '2026-08-24'
references:
- title: Development and Deployment at Facebook
  year: 2013
  tier: III
  url: https://www.cs.huji.ac.il/w~feit/papers/FB13IC.pdf
  kind: publication
  authors: Dror G. Feitelson, Eitan Frachtenberg, Kent L. Beck
  venue: IEEE Internet Computing 17(4)
- title: Envoy shadow
  kind: tool
  url: https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/cluster/cluster#shadow
  description: Envoy proxy shadow traffic mirroring
- title: diffy
  kind: tool
  url: https://github.com/twitter/diffy
  description: Differential proxy for API testing
---

Run the new implementation against real inputs without affecting users. A
sensor that produces *differential evidence* with zero user risk.

Shadow traffic mirrors real requests to the new version, discards the
responses, and compares the new version's behavior to the old. It's
[differential testing](differential-testing.html) with real production
inputs.

## In practice

A typical reading is the comparison report after a mirroring window:

| Measure | Baseline | Candidate | Divergence |
|---------|----------|-----------|------------|
| 2xx rate | 99.9% | 99.2% | -0.7pp, FAIL |
| p95 latency | 122 ms | 141 ms | +16%, watch |
| body diff rate | | 0.4% of requests | classify |

```
sample divergent request 8f31e2:
  endpoint:  GET /v2/orders/10482
  baseline:  200  {"status":"shipped","items":[...]}
  candidate: 200  {"items":[...],"status":"shipped"}
  diff:      field ordering only (benign)
```

Reading it well:

- **Classify before counting.** A 0.4% diff rate is alarming or trivial
  depending on whether the diffs are wrong answers or field ordering and
  timestamps. The report is only as good as its classifier.
- **Trust the inputs, check the coverage.** Mirroring guarantees the same
  input distribution, but confirm the window contained the rare shapes:
  month-end batches, enterprise accounts, retry storms.
- **Watch the side-effect line.** A shadow that writes to the real
  database or charges the real card is not shadowing. Isolation is the
  precondition that makes the whole sensor honest.

## How it gets gamed

Shadow traffic runs on real inputs, but the verdict is still read by
people who want the deploy to land:

- **Divergences classified benign in bulk.** Field ordering, timestamps,
  and rounding are genuinely harmless diffs, and "it's just ordering" is
  the easiest blanket rationale for a report nobody wants to read item by
  item. A divergence rate that falls after reclassification, not after a
  code change, is the tell.
- **Mirroring only the easy traffic.** Routing only idempotent GETs, or
  only internal test accounts, through the shadow gives the candidate a
  gentler exam than production will give it. Check the shadow's input
  distribution against real traffic before trusting the verdict.
- **Short windows.** A ten-minute mirror window that contains no rare
  payloads, month-end shapes, or retry storms will report clean, and the
  report will be technically true.
- **Ignoring the side-effect audit.** Divergence reports get read; the
  question "did the shadow write anything real?" often does not. Skipping
  that audit is how a zero-risk sensor becomes a risk.

The meta-signal is the share of divergent requests classified as benign
without an inspected sample. If it approaches 100%, the comparison is a
formality.

## Response playbook

When the shadow comparison report shows divergence:

1. **Classify the divergences before reacting.** Pull a sample of the
   divergent request pairs and sort them: wrong answers, missing fields,
   ordering, timestamps, errors. The category, not the count, decides
   what to do next.
2. **Reproduce one divergence locally.** Take a single divergent input,
   run it against both versions, and find the mechanism. One reproduced
   case is worth a thousand sampled pairs.
3. **Check the side-effect line immediately.** Verify the shadow run
   wrote nothing to real storage and made no external calls it should
   not have. If isolation broke, that is the incident, ahead of any
   divergence question.
4. **Decide the gate.** If the divergences are wrong answers, block the
   promotion and fix; if they are benign noise, improve the classifier
   so the next run reports them separately, and record why they were
   accepted.
5. **Re-run the mirror after the fix.** Shadow traffic is cheap and
   reproducible; a second window after the fix closes the loop without
   spending any user risk.

## What it cannot detect

Shadow traffic can only compare what both versions produce. If both have
the same bug, it won't be detected. Also, side effects (database writes,
external calls) must be carefully isolated.
