---
order: 30
kind: composition
title: "A minimal stack for a batch or data pipeline"
shape: >-
  Scheduled jobs that read, transform, and write data. Wrong output is
  silent, and someone downstream discovers it weeks later.
stack:
  - sensor: schema-validator
    closes: [not-internally-consistent]
    why: Validate on read and on write; upstream shapes drift between runs.
  - sensor: snapshot-tests
    closes: [unintended-change]
    why: Golden output on a fixed input catches a transform that moved.
  - sensor: metamorphic-testing
    closes: [wrong-logic]
    why: The right output is unknown; a rerun must still not change it.
  - sensor: mutation-testing
    closes: [unasserted-execution]
    why: Transform tests that assert nothing let wrong output through silently.
  - sensor: smoke-tests
    closes: [does-not-run-where-deployed]
    why: One partition through the real scheduler and credentials first.
  - sensor: database-invariants
    closes: [unjudged-observation]
    why: The engine checks every row written; nothing to schedule or scrub.
  - sensor: load-testing
    closes: [cannot-carry-load]
    why: Run it at the biggest day's volume; falling behind is the failure.
left_open:
  - doubt: dependency-failure
    reason: >-
      A job that dies when its source is down and reruns from its
      checkpoint is the degradation you want. Spend on idempotent reruns
      before spending on fault injection.
  - doubt: untested-conditions
    reason: >-
      Both closers split live traffic between two versions, and a
      scheduled job has no traffic to split.
  - doubt: emergent-failure
    reason: >-
      Stages hand off through the store, and the schema row validates
      each handoff. Add integration tests when a stage starts talking to
      something other than the store.
---

A service reports its own failure with a 500. A pipeline reports nothing;
the wrong rows land and the next job reads them. So most of this stack runs
before the job is scheduled, and the two rows that run in production, the
[schema check](schema-validator.html) and the [database
constraints](database-invariants.html), both refuse the write, so the bad
row never lands for anyone to discover.
