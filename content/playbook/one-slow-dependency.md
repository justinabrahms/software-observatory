---
order: 70
kind: symptom
title: "One slow dependency took everything down"
noticed: >-
  A cache or a third-party API got slow. Nothing about your service
  changed. Within minutes every request was timing out, the connection
  pools were full, and the whole thing was down.
doubt: dependency-failure
sensor: fault-injection
---

## Point this at it

[Fault injection](fault-injection.html), one experiment, in staging.
Use Chaos Mesh, Litmus, or Gremlin to inject latency into the dependency
that caused the last incident, at the magnitude it actually had. If it
paused for two seconds, inject two seconds; fifty milliseconds tests your
timeout config and nothing else.

Before you start, write the steady-state hypothesis down: p99 latency
under a number, error rate under a number, zero lost writes. Give the run
a ramp, five minutes of fault, and a recovery window, and watch each
invariant during the fault. Without the invariants the run passes by
definition.

## Reading it

- Red: an invariant broke under that fault. File it with the exact fault
  and the invariant, and read the secondary symptoms, since they usually
  name the weakness: a retry storm, a missing timeout, a hidden hard
  dependency. Fix the weakest coupling, then re-run the same experiment
  to prove the fix.
- Green: the system kept its invariants under this one fault at this one
  magnitude. One survived fault is a data point, and the next run should
  be a different fault or a compound one.
- It does not prove anything about failure modes you did not think to
  inject, and a staging run without production traffic never sees the
  ones that hurt most.

## If the doubt survives

If every fault you inject passes and the outages continue, the trigger is
something production has and staging does not: the real traffic mix, the
real data shapes, a failure combination you did not model. That is
untested conditions, and it is closed on real traffic by
[canary analysis](canary-analysis.html) or
[shadow traffic](shadow-traffic.html) rather than by another staging run.
