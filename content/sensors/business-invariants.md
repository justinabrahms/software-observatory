---
id: SO-004c
title: Business Invariants
family: invariants
family_num: '04'
oracle: high
oracle_note: 'a violation means the business is broken'
independence: high
independence_note: 'observes outcomes, not implementation'
scope: system
scope_note: 'domain level'
latency: hours
actionability: guiding
actionability_note: "17 payments have no order transition"
type: retrospective
stack_level: user-outcome
categories:
- Invariants
- Domain Correctness
- Black-Box Sensors
see_also:
- SO-004
- SO-004b
- SO-006
last_reviewed: 2026-08-23
references:
- title: Great Expectations
  url: https://greatexpectations.io
  kind: tool
  description: Python data quality testing
- title: Soda
  kind: tool
  url: https://docs.soda.io
  description: Data quality testing and monitoring
- title: dbt tests
  kind: tool
  url: https://docs.getdbt.com/docs/build/tests
  description: Data transformation testing
---

A successful payment implies an order eventually becomes paid.
`order.total == sum(line_items)`. These are *domain-level correctness*
sensors that need no knowledge of the implementation.

Business invariants are the highest-level invariant sensor: they check
whether the system is accomplishing its business purpose, not just whether
its internals are consistent. They require [observability
events](observability-events.html) as a data source.

## In practice

A reading is a batch report over the last window of business events,
one row per invariant, each with a verdict:

| Invariant | Window | Expected | Observed | Verdict |
|-----------|--------|----------|----------|---------|
| payment implies paid order | 24 h | 0 violations | 17 | FAIL |
| order.total == sum(line_items) | 24 h | 0 violations | 0 | pass |
| refund <= original charge | 24 h | 0 violations | 3 | FAIL |
| signup answered with welcome email within 1 h | 24 h | >= 99% | 97.1% | FAIL |

The report reads like a balance sheet for the domain: each row states a
promise the business makes and whether the last window kept it.

Reading it well:

- **Violations are business facts, not technical ones.** Seventeen
  payments with no paid order means finance reconciles incorrectly
  this week. Route the finding to the domain owner, not just the
  on-call engineer.
- **Compare against the previous window before escalating.** A new
  violation class is an incident; a stable trickle may be a known edge
  case. The delta is the signal.
- **An empty row deserves suspicion.** An invariant that has never
  failed in six months is either very healthy or no longer running.
  Spot-check the query.

## How it gets gamed

Business invariants are queries someone wrote, on data someone controls:

- **Tune the threshold until it passes.** The invariant becomes
  "violation rate above 2%," and 2% keeps rising. A business promise
  with a tolerance band is a suggestion.
- **Change the counting.** Classify the violating payments as refunds,
  test data, or known exceptions, and the violation count falls
  without the business improving. The definition, not the system,
  absorbed the fix.
- **Delay the window.** If the check runs over the last 24 hours,
  push the offending events just past the edge of the window, or slow
  the event pipeline so the report lags the damage.
- **Underfund the feed.** The checker reads the same
  [observability events](observability-events.html) as everything
  else; quietly dropping a field it needs makes the invariant
  uncomputable, which reads as "no data," not "broken."

The meta-signal is the exception list. Every invariant with a growing
carve-out is a promise being renegotiated without anyone admitting it.

## Response playbook

When a business invariant fails:

1. **Confirm the violation is real before escalating.** Run the query
   by hand against the same window. A stale pipeline, a late event
   batch, or a schema rename can produce violations that never
   happened. The check is only as good as its feed.
2. **Route to the domain owner, not just on-call.** Seventeen
   payments with no paid order is a finance problem wearing an
   engineering costume. The person who owns the business process
   decides whether the violation is a bug, an edge case, or a policy
   question.
3. **Compare against the previous window.** A new violation class is
   an incident. A stable trickle that has existed for months is a
   known gap; fix it, but do not treat it as a regression.
4. **Decide the remediation explicitly.** Some violations need data
   repair, some need a code fix, and some need the invariant itself
   redefined because the business rule changed. Write down which one
   you chose; the next reading will be compared against that choice.
5. **Feed the failing case back into the pipeline.** A business
   invariant that fired in production is a specification for a
   [runtime invariant](runtime-invariants.html) or a test that should
   have caught it earlier. Move the detection left.

## What it cannot detect

Business invariants can only check properties you *thought to specify*. They
don't find unknown unknowns — that's what [observability](observability-events.html)
is for.
