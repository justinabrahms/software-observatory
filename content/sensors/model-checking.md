---
id: SO-016
title: Model Checking
family: structural
family_num: '01'
oracle: maximum
oracle_note: an exhaustive search of the state space is a proof
independence: high
independence_note: the checker explores states the author did not think to write tests for
scope: system
scope_note: the model, not the implementation
latency: minutes
latency_note: minutes to hours for non-trivial specs
actionability: blocking
actionability_note: a counter-example trace stops the spec from shipping
type: predictive
stack_level: static-analysis
categories:
- Structural
- Formal Methods
see_also:
- SO-012
- SO-013
- SO-001
- SO-001e
- structural
last_reviewed: '2026-08-24'
references:
- title: 'How Amazon Web Services Uses Formal Methods'
  year: 2015
  tier: III
  url: https://cacm.acm.org/research/how-amazon-web-services-uses-formal-methods/
  kind: publication
  authors: Chris Newcombe, Tim Rath, Fan Zhang, Bogdan Munteanu, Marc Brooker, Michael Deardeuff
  venue: Communications of the ACM 58(4)
- title: 'TLA+ Model Checking Made Symbolic'
  year: 2022
  tier: III
  url: https://link.springer.com/chapter/10.1007/978-3-031-22465-5_8
  kind: publication
  authors: Markus Kuppe
- title: 'Practical Model Checking for Software'
  year: 2023
  tier: IV
  url: ''
  kind: publication
  description: Spin, NuSMV, and the case for exhaustive state-space search in industry
- title: TLA+
  url: https://lamport.org/tla/tla.html
  kind: tool
  description: Specification language and model checker (TLA Toolbox)
- title: Alloy
  url: https://alloytools.org
  kind: tool
  description: Lightweight relational specification and analysis
- title: Spin
  url: https://spinroot.com
  kind: tool
  description: Explicit-state model checker for distributed systems
- title: NuSMV
  url: https://nusmv.fbk.eu
  kind: tool
  description: Symbolic model checker for finite-state systems
- title: Apalache
  url: https://apalache.informal.systems
  kind: tool
  description: Symbolic model checker for TLA+
---

Exhaustive exploration of a system's reachable states against a temporal
property. Where a [type checker](type-checker.html) proves a property holds
for one step, and [statically checked invariants](statically-checked-invariants.html)
prove a property holds for all executions of a function, a model checker
proves a property holds across every reachable state of a *system model* —
every message order, every crash, every interleaving of concurrent actions.

The model is not the implementation. The gap between "the spec is correct"
and "the code implements the spec" is the sensor's central limit, and it is
the same limit that makes it tractable: you check a faithful abstraction of
the system, not the system itself, which is why the state space is finite
enough to exhaust.

## In practice

A reading is a counter-example trace — the minimal sequence of steps that
reaches a state violating the property:

```
APALACHE
State 1: [ state = Idle, queue = <<>> ]
State 2: [ state = Processing, queue = <<Req>> ]
State 3: [ state = Processing, queue = <<>> ]  -- dequeued
State 4: [ state = Done, queue = <<>> ]
Violation: Invariant NoDoubleProcess at State 4
  Action: ProcessTwice
  The invariant 'at most one process per request' is violated.
```

The counter-example is the reading's value. A failing test tells you a
case broke; a model-checker counter-example tells you the *exact sequence*
of events that broke it, including interleavings a test suite would never
generate. Triage is fast because the trace is minimal and reproducible.

## Response playbook

When a counter-example appears:

1. **Replay the trace.** The checker emits the minimal violating sequence;
   read it before reading the property.
2. **Decide whether the model or the property is wrong.** A counter-example
   is a genuine disagreement between two claims the author made. One must
   be retracted.
3. **If the model is right, fix the implementation.** The trace tells you
   which interleaving the code doesn't handle.
4. **If the property is too strong, weaken it — and document why.** A
   property that was "at most one process" becoming "at most two" is a
   real change to the system's contract, not a tidy-up.

## How it gets gamed

The checker cannot be gamed, but the model can be degraded:

- **Under-model the system.** Drop the failure modes that produce the
  counter-examples — no crashes, no retries, no clock skew — and the
  checker passes because it is exploring a simpler world than the one
  that ships.
- **Over-abstract the state.** Collapse the state space until the
  property trivially holds. A model with one state cannot violate a
  liveness property.
- **Check the happy path only.** Initialize the model with the inputs
  the author expected, not the inputs the system can receive.
- **Verification off the merge path.** A model-checking job that runs
  nightly or on demand, rather than on every spec change, is a proof
  nobody is waiting for.

The meta-signal is model fidelity: sample the spec and count how many
failure modes are represented. A spec that models only the happy path
will have a clean check and protect nothing.

## What it cannot detect

Model checking cannot detect that the implementation matches the model.
The spec is written by the same mind that writes the code, so a model
that checks clean against a wrong spec is a proof of the wrong thing.
This is why model checking composes with rather than replaces
[example-based tests](example-based-tests.html) and
[observability events](observability-events.html) — the model proves
the spec, the tests check the implementation, and production
observability catches what neither anticipated.

Model checking also cannot scale to unbounded state spaces without
abstraction; the choice of what to abstract away is where the author's
assumptions enter, and a counter-example that survives abstraction is
stronger evidence than one that depends on the abstraction being exact.
