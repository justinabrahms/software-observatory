---
order: 10
kind: starting-point
title: "You have green CI and nothing from production"
where: >-
  Compiler, linter, unit tests, a coverage number. Every merge is green.
  The first you hear of a bug is a user telling you about it.
have:
  - compiler
  - linter
  - example-based-tests
  - line-coverage
steps:
  - sensor: smoke-tests
    closes: [does-not-run-where-deployed]
    why: >-
      Nothing you run today touches the deployed artifact. Four requests
      against the fresh deploy, one per vital sign, take an afternoon to wire
      up and close the doubt that the thing you tested is the thing that is
      running.
  - sensor: observability-events
    reveals: [unspecified-property]
    why: >-
      Closes nothing before shipping. It is the only sensor on this list
      that reveals unspecified property, which is where the bugs your users
      report currently live, and it is the data the next step and the last
      step both read from.
  - sensor: business-invariants
    closes: [unjudged-observation]
    why: >-
      The events from the previous step say what happened; nothing yet says
      whether it was right. One query per domain promise over those events
      is the judge the events lack, and it runs on real data rather than on
      the cases your unit tests thought to try.
  - sensor: mutation-testing
    closes: [unasserted-execution]
    why: >-
      Fourth because it tells you nothing new about the system; it improves
      the tests you already have. Your coverage number counts lines that
      ran, and this is the first step that asks whether any test would
      notice if those lines returned the wrong answer.
  - sensor: canary-analysis
    closes: [untested-conditions, emergent-failure, unintended-change]
    why: >-
      Three doubts from one sensor, and it depends on steps two and three:
      the events supply the metrics it compares between versions, and the
      invariants supply the violations that count as a divergence. Without
      them the canary has a tolerance band and nothing to apply it to.
skip:
  - sensor: branch-coverage
    reason: >-
      Same doubt as line coverage. It tells you which side of a conditional
      never ran, and still says nothing about whether the side that ran was
      asserted on.
---
