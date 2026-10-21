---
id: SO-012d
title: Escaped Defect Rate
family: test-effectiveness
family_num: '03'
oracle: medium
oracle_note: classification of "should have caught" is judgment
independence: high
independence_note: production failures cannot be gamed by the suite
scope: system
latency: months
actionability: guiding
actionability_note: points at the layers of the suite that leak
type: retrospective
stack_level: user-outcome
categories:
- Test Effectiveness
see_also:
- SO-003
- SO-009c
- SO-012c
---

Of the bugs that reached users, which ones should the test suite have
caught? Escaped defect rate is the slowest and most honest measure of test
effectiveness: not "would the tests catch a hypothetical mutant?" but "did
they catch the actual failures, judged after the fact?"

## In practice

Illustrative monthly review, using a fixed definition: confirmed defects
first discovered in production divided by all confirmed defects first
discovered during the month. Deduplicate reports before counting them.

| First discovered | Confirmed defects |
|------------------|-------------------|
| Before production | 32 |
| In production | 8 |
| Total | 40 |

The escaped share is 8 / 40, or 20%. This is a discovery cohort, not a
measurement of the probability that a release contains a bug: some of the
eight escapes may have shipped months earlier. Keep the raw counts and
severity breakdown alongside the percentage. A change in reporting or
classification can move it without any change in the software.

## Response playbook

When the rate rises, the move is classification, not blame:

1. **Triage by layer.** For each escaped defect, ask which sensor should
   have caught it. A null-reference crash is a [type
   checker](type-checker.html) miss. A wrong total is a missing
   [behavioral test](integration-tests.html). A slow query that only
   surfaced in production is a [profiling](continuous-profiling.html) gap.
2. **Add the sensor, then the test.** If a class of defect keeps escaping,
   the suite has a structural hole that one more hand-written test will
   not fill. Repeat escapes of the same class — two injections in a
   quarter — mean the right sensor, here [static security
   analysis](static-security-analysis.html), belongs in the pipeline.
3. **Require a regression test before the fix.** Every escaped defect is a
   free test case: the production failure is the specification.
4. **Do not manage to the number.** The rate lags by months and the
   classification is judgment. Optimizing it directly produces re-labeling,
   not better sensors. Pair it with [mutation
   testing](mutation-testing.html) as the fast leading indicator.

## How it gets gamed

- **Relabel the escape.** Call a production bug a support request or an
  enhancement so it leaves the numerator without changing the product.
- **Change the denominator.** Split releases or count smaller work items to
  improve a per-release rate while the same number of defects reaches users.
- **Close before classifying.** Resolve incidents without linking the defect
  and the sensor that missed it, leaving the hardest cases uncounted.

The meta-signal is the fraction of production incidents with no linked
defect classification, plus changes to severity and denominator rules.

## What it cannot detect

Defects nobody reported, and defects attributed to the wrong cause. It also
lags badly: it tells you about the suite you had, not the suite you have.
Pair it with [mutation testing](mutation-testing.html) for a fast proxy and
with [incident correlation](incident-correlation.html) for the cost side.
