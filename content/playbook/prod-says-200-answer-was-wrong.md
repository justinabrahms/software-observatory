---
order: 30
kind: symptom
title: "Production says 200 and the answer was wrong"
noticed: >-
  Dashboards were green all week. Latency fine, error rate zero. Then
  finance found orders that were paid and never marked paid, and every
  one of them had been logged as a success.
doubt: unjudged-observation
sensor: business-invariants
next: bugs-in-inputs-nobody-tried
---

## Point this at it

[Business invariants](business-invariants.html), one query, over the
last 24 hours, for the promise that just broke. Write it against the
events or tables you already have and run it once a day from a
scheduled job: a dbt test, a Great Expectations suite, or a cron job
with SQL in it. "Every payment event has an order in state paid within
an hour" with an expected violation count of zero.

Every term has to name a field someone can point at. "The order total is
right" cannot be queried, so whoever implements it picks a weaker
reading, and that row passes without testing the promise you meant. The
feed is your existing observability events; if the fields the query
needs are not being emitted, that is the first fix.

## Reading it

- Red: a violation count. Run the query by hand against the same window
  before escalating, since a late batch or a schema rename produces
  violations that never happened. Then route it to the domain owner. A
  new violation class is an incident; a trickle that has been there for
  months is a known gap.
- Green: zero violations of this promise in this window. A row that has
  never failed in six months deserves a check that it is still running.
- It does not prove anything about promises you did not write down, and
  it reads hours after the damage rather than before it.

## If the doubt survives

The invariant tells you the answer was wrong; it says nothing about why.
When you trace the violating rows back into the code, the usual finding
is a function that returns the wrong result for inputs the tests never
supplied. That is wrong logic, and the next play is for it.
