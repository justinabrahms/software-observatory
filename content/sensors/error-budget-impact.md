---
id: SO-007d
title: Error-Budget Impact
family: change
family_num: '07'
oracle: medium
oracle_note: budget burn is correlated, not causal
independence: high
independence_note: production measurements
scope: system
latency: hours
actionability: guiding
actionability_note: this deployment burned 30% of the monthly budget
type: retrospective
stack_level: user-outcome
categories:
- Change
- Production Sensors
see_also:
- SO-007
- SO-007b
- evolution-family
last_reviewed: '2026-08-24'
references:
- title: Google SRE Workbook
  url: https://sre.google/workbook/error-budget/
  kind: tool
- title: SLO dashboards
  kind: tool
  url: https://sre.google/workbook/alerting-on-slos/
  description: Service level objective tracking dashboards
- title: error budget calculators
  kind: tool
  url: https://sre.google/workbook/error-budget/
  description: Error budget tracking tools
---

Did this change consume an abnormal amount of reliability budget? A sensor
that directly ties code changes to user-visible impact.

An error budget is the allowed amount of unreliability over a period (e.g.,
99.9% uptime = 43 minutes of downtime per month). Error-budget impact
measures whether a specific deployment consumed a disproportionate share of
that budget — connecting code changes to [user outcomes](catalog.html#evolution).

## In practice

An error-budget reading is a burn number tied to a time window, usually
on the SLO dashboard next to the deployment timeline:

| Metric | Value |
|--------|-------|
| SLO | 99.9% success over 30 days |
| Budget for the window | 43.2 minutes of errors |
| Consumed by v2.41.0 rollout (14:02-14:47) | 27 minutes |
| Budget burned by this change | 62% |
| Remaining budget | 16.2 minutes |

The core reading is attribution: which deployment, feature, or incident
ate the budget, and how much. Reading it well:

1. **Read burn rate, not totals.** The budget drains a little every
   day. What matters is the slope change at the deploy timestamp, not
   the cumulative number in isolation.
2. **Compare burn to the change size.** A routine release should burn
   almost nothing. A change that consumes a third of the monthly budget
   has bought its way into production with reliability as the currency.
3. **Check the window before judging.** A budget at 5% remaining in the
   last two days of the window is a different reading than at the start
   of it. Exhaustion is what triggers consequences, not the burn alone.
4. **Correlation is the sensor's limit.** The deploy and the burn
   coinciding is evidence, not proof. Cross-check against
   [canary analysis](canary-analysis.html) and the deployment timeline
   before assigning the cost to one change.

## How it gets gamed

The burn itself comes from production and cannot be faked, but the
budget is a policy number, and policy is where the gaming happens:

- **SLO shopping.** When the budget runs out, the fix becomes relaxing
  the SLO: 99.9% becomes 99.5%, or the error class in question is
  excluded from the indicator. The budget resets without anything
   becoming more reliable.
- **Error reclassification.** Failures get labeled "client errors" or
  "expected churn" and leave the numerator. The dashboard improves
  while users see the same behavior.
- **Budget laundering across windows.** Burning the budget at the end
  of one window and counting the reset as fresh starts, so the
   consecutive cost of unreliable changes never accumulates anywhere.

The meta-signal is the SLO change history. Every relaxation of a target
or redefinition of an error class should be reviewed like a rule change
to a [computational gate](computational-gates.html), because that is
what it is.

## Response playbook

When a change burns budget or the budget runs out:

1. **Attribute the burn before acting.** Line the burn curve up with the
   deployment timeline and confirm the change that started it. If the
   correlation is weak, stop there and investigate rather than
   penalizing a release that only looks guilty.
2. **Roll back if the burn is ongoing.** A change still consuming
   budget is costing users right now. Reverting restores the budget
   immediately; the [revert rate](revert-rate.html) absorbs the mark,
   and that is the correct trade.
3. **Halt feature launches when the budget is exhausted.** The budget
   is the agreed price of unreliability; when it is spent, new risk is
   paused and effort shifts to reliability until the window resets.
4. **Charge the burn to the change that caused it.** Record the
   deployment that consumed the budget next to the incident, so the
   next release decision sees the cost of the last one.
5. **Tighten the rollout for the next change.** A budget-hungry
   deployment should come back with a smaller canary slice and
   [canary analysis](canary-analysis.html) thresholds checked before it
   is allowed to burn at scale again.

## What it cannot detect

Error-budget impact shows correlation between deployment and reliability
degradation, but not causation. Other factors (traffic patterns, upstream
failures) may contribute.
