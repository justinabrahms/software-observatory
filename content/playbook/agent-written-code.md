---
order: 30
kind: starting-point
title: "You ship agent-written code faster than you can read it"
where: >-
  An agent writes the change and the tests for it. The compiler and type
  checker pass, the tests pass, and you merged more today than you read.
have:
  - compiler
  - type-checker
  - example-based-tests
steps:
  - sensor: second-agent-review
    closes: [wrong-specification, missing-behavior]
    why: >-
      Everything you have so far was produced by the author. A different
      model, shown the diff and never the author's summary, is the cheapest
      check on whether the change does what was asked and whether anything
      asked for is absent, and it runs at the speed you are merging.
  - sensor: independent-review
    closes: [correlated-blind-spot]
    why: >-
      Two models from one lineage agree on the same wrong answer, so the
      previous step cannot close correlated blind spot. A human who reads
      the specification and then the code, on a sample of merges, is the
      only closer of that doubt in the catalog.
  - sensor: mutation-testing
    closes: [unasserted-execution]
    why: >-
      The tests being judged were written by the agent that wrote the code,
      and an agent will call every function and assert on none of them.
      Each surviving mutant is a test that ran the line and never checked
      it; on an agent-written suite, expect the survivor list to be long.
  - sensor: fitness-functions
    closes: [structure-decayed]
    why: >-
      An agent takes the shortest path to a passing test, and the shortest
      path is often an import the architecture forbids. A handful of
      dependency rules, run in CI, fail on the exact edge the change added,
      and they are the only step here that reads the structure rather than
      the behaviour.
  - sensor: canary-analysis
    closes: [untested-conditions, emergent-failure, unintended-change]
    why: >-
      Every step above judges the change on its own. Routing a few percent
      of real traffic to it and comparing error rate and latency against the
      old version, with tolerances set in advance, is the one step that sees
      the change wired into the system under traffic nobody wrote a test for.
skip:
  - sensor: line-coverage
    reason: >-
      An agent will happily execute every line without asserting anything,
      and coverage counts executed lines. The number will be high and mean
      nothing; mutation testing is the reading you wanted from it.
---
