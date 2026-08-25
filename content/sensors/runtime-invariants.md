---
id: SO-004
title: Runtime Invariants
family: invariants
family_num: 4
oracle: high
oracle_note: a violation is definitive evidence of a bug
independence: medium
independence_note: assertions are written by the same author, but run against production reality
scope: system
scope_note: domain level
latency: seconds-hours
latency_note: batch to real-time
actionability: guiding
actionability_note: 17 payments have no order transition
type: retrospective
type_note: detects violations after they occur
stack_level: production-behavior
categories:
- Invariants
- Domain Correctness
- Production Sensors
- Black-Box Sensors
see_also:
- SO-001
- SO-006
- adversarial
- behavioral
last_reviewed: '2026-08-24'
references:
- title: 'Detecting Data Errors: Where are we and what needs to be done?'
  year: 2016
  tier: I
  url: https://www.vldb.org/pvldb/vol9/p993-abedjan.pdf
  kind: paper
  authors: Ziawasch Abedjan, Xu Chu, Dong Deng, Raul Castro Fernandez, Ihab F. Ilyas, Mourad Ouzzani, Paolo Papotti, Michael Stonebraker, Nan Tang
  venue: PVLDB 9(12)
- title: 'AddressSanitizer: A Fast Address Sanity Checker'
  year: 2012
  tier: III
  url: https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/37752.pdf
  kind: paper
  authors: Konstantin Serebryany, Derek Bruening, Alexander Potapenko, Dmitry Vyukov
  venue: USENIX ATC '12
- authors: Hoare
  title: An Axiomatic Basis for Computer Programming
  year: 1969
  kind: paper
  tier: IV
- title: assertpy
  kind: tool
  url: https://github.com/assertpy/assertpy
  description: Python fluent assertion library
- title: pytest-check
  kind: tool
  url: https://github.com/okken/pytest-check
  description: Non-blocking assertions for pytest
- title: Hypothesis invariants
  kind: tool
  url: https://hypothesis.readthedocs.io/en/latest/quickstart.html
  description: Using Hypothesis for invariant checking
---

You don't need to know how the payment service works. You can observe:
*"5,213 payments occurred; 17 have no corresponding order transition."* That's
a sensor of correctness without understanding the implementation. That is
enormously powerful.

## What must always be true

Instead of specifying examples — given X, expect Y — specify things that
must *always* be true. These are invariants, and they operate at multiple
levels:

```
account balance >= 0
order.total == sum(line_items)
created_at <= updated_at
every foreign key refers to an existing object
a successful payment implies an order eventually becomes paid
every request has exactly one request_id
```

Each invariant can be checked at compile time, test time, CI, runtime, in
the database, or in production analytics. Each is a different sensor at a
different cost point and latency.

> Runtime invariants become sensors of correctness without understanding
> the implementation. You don't need to read the code. You need to observe
> the event stream and ask: does this invariant hold?

## In practice

A reading is a violation event from the checker watching the event
stream, naming the invariant, the count, and enough keys to investigate:

```
INVARIANT VIOLATION  payments_reconcile
rule:     every successful payment implies an order transition to paid
window:   2026-08-19T00:00Z .. 2026-08-19T06:00Z
violated: 17 of 5213 payments (0.33%)
sample:   payment_id=p_9f2c order_id=o_1187 (no transition)
          payment_id=p_9f31 order_id=o_1202 (no transition)
```

Three habits for reading it well:

- **Read the denominator first.** Seventeen violations is an incident
  if the window held two hundred payments and noise if it held five
  million. The rate, not the count, decides urgency.
- **Sample keys are for tracing, not counting.** The listed IDs lead
  into traces and logs where the cause lives; the count tells you the
  size. Neither answers alone.
- **A silent invariant is a broken one.** If the checker has not
  reported in its expected window, assume it stopped reading the
  stream before assuming the system got correct. The feed it depends
  on is the [observability events](observability-events.html) layer.

## How it gets gamed

Invariants are checked by software, and software is configured by the
same people shipping the changes they check:

- **Silence the alert, keep the rule.** The checker still runs and the
  dashboard still updates, but nobody is paged. The violation count
  climbs in a tab nobody opens.
- **Narrow the scope.** The check now excludes a tenant, a region, or
  a time window where it "fires too often," and the excluded slice is
  exactly where the risky change lives.
- **Loosen the threshold.** Seventeen violations becomes "violation
  rate above 1%," which passes, and the bar keeps rising as the
  system degrades.
- **Fix the symptom, not the write.** Violating rows get scrubbed
  before the nightly check runs. The invariant passes; the cause is
  still writing bad data.

The meta-signal is the violation rate before any exclusion, kept next
to the size of the exclusion list. If exclusions grow while the rate
falls, the sensor is being tuned out of existence.

## Response playbook

When an invariant violation fires:

1. **Triage by the denominator, not the count.** Seventeen violations
   out of two hundred payments is a stop-the-world event; out of five
   million it is a ticket. Compute the rate before paging anyone.
2. **Trace the sample keys.** The listed IDs lead into traces, logs,
   and the event stream. Follow one end-to-end before generalizing;
   the first sample usually reveals the mechanism, and the mechanism
   tells you whether the remaining violations share a cause.
3. **Determine whether the write path is still open.** If the cause
   is a running deploy or a batch job in flight, stop it. An
   invariant that fires while the cause keeps writing will keep
   firing; investigate the backlog after the tap is closed.
4. **Reconcile the affected records.** Once the cause is stopped,
   decide which violations are repairable in place and which need
   manual review. Mark the unrepaired ones so the next invariant run
   does not re-alert on them forever.
5. **Write the failing case into the test suite.** The production
   violation is a specification. The same invariant, checked against
   recorded events, belongs in CI so the next version fails before it
   ships.

## What it cannot detect

Runtime invariants can only check properties you *thought to specify*. They
don't find unknown unknowns — that's what [observability
events](observability-events.html) are for. They also can't tell you *why*
an invariant was violated, only that it was.
