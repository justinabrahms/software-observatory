---
order: 10
kind: composition
title: "A minimal stack for a request-serving service"
shape: >-
  HTTP or RPC in, a database and a few dependencies behind, deployed
  continuously.
stack:
  - sensor: type-checker
    closes: [not-internally-consistent]
    why: Milliseconds, definitive, and the diagnostic names both sides.
  - sensor: mutation-testing
    closes: [unasserted-execution]
    why: The only closer. Run it on the modules that bill or authorize.
  - sensor: integration-tests
    closes: [emergent-failure]
    why: Against the real database, before merge; a canary sees it too late.
  - sensor: smoke-tests
    closes: [does-not-run-where-deployed]
    why: Four requests against the fresh deploy, before real traffic arrives.
  - sensor: fault-injection
    closes: [dependency-failure]
    why: In staging, at realistic magnitude; live chaos is the same technique later.
  - sensor: business-invariants
    closes: [unjudged-observation, wrong-logic]
    why: Says whether the 200 was the right answer, in the domain's terms.
  - sensor: canary-analysis
    closes: [untested-conditions, unintended-change]
    why: Two doubts, one sensor, on traffic you already have.
  - sensor: error-budget-impact
    reveals: [late-effects]
    why: Retrospective, but it charges the burn to the deploy that caused it.
left_open:
  - doubt: cannot-carry-load
    reason: >-
      Until there is a load number to aim at. A load test run at a
      concurrency the service already serves asks nothing.
  - doubt: wrong-specification
    reason: >-
      Only review closes it, and review is a practice you run rather than
      a thing you install.
  - doubt: correlated-blind-spot
    reason: >-
      Same closer, independent review. The canary compares the new
      version against the old one, so a bug both versions share reads
      green; review is where that gets caught.
---

Install the merge gates first: the type checker and the integration suite
are an afternoon each. The canary and the business invariants both read
from the same observability events, so those two arrive together once the
events exist. Fault injection comes last, because its verdict is only as
good as the invariants it checks against, and until then a passing run
proves nothing.
