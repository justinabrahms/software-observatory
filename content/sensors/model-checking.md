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
- SO-017
- structural
last_reviewed: '2026-08-28'
references:
- title: 'How Amazon Web Services Uses Formal Methods'
  year: 2015
  tier: III
  url: https://cacm.acm.org/research/how-amazon-web-services-uses-formal-methods/
  kind: publication
  authors: Chris Newcombe, Tim Rath, Fan Zhang, Bogdan Munteanu, Marc Brooker, Michael Deardeuff
  venue: Communications of the ACM 58(4)
- title: TLA+ Model Checking Made Symbolic
  year: 2019
  tier: III
  url: https://dl.acm.org/doi/10.1145/3360549
  kind: publication
  authors: Igor Konnov, Jure Kukovec, Thanh-Hai Tran
  venue: Proceedings of the ACM on Programming Languages 3 (OOPSLA)
- title: The Model Checker SPIN
  year: 1997
  tier: IV
  url: https://spinroot.com/spin/Doc/ieee97.pdf
  kind: publication
  authors: Gerard J. Holzmann
  venue: IEEE Transactions on Software Engineering 23(5)
  description: The design of an explicit-state checker and the case for exhaustive
    state-space search
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
reaches a state violating the property. The checker's console says only
where it broke and where to look:

```
State 3: state invariant 0 violated.
Check the counterexample in: _apalache-out/MCQueue.tla/counterexample1.tla
```

The trace itself is the file, written as a runnable module — one
definition per state, and the violating formula at the end:

```
---------------------------- MODULE counterexample ----------------------------

EXTENDS MCQueue

(* Initial state *)
State0 ==
processed = 0
/\ queue = <<>>
/\ state = "Idle"

(* Transition 0 to State1 *)
State1 ==
processed = 0
/\ queue = <<"Req">>
/\ state = "Processing"

(* Transition 1 to State2 *)
State2 ==
processed = 1
/\ queue = <<>>
/\ state = "Processing"

(* Transition 2 to State3 *)
State3 ==
processed = 2
/\ queue = <<>>
/\ state = "Done"

(* The following formula holds true in the last state and violates the invariant *)
InvariantViolation == processed > 1

================================================================================
```

The request was dequeued once and processed twice, and the trace names
the transition that did it.

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
- **Over-abstract the state.** Collapse the state space until there is
  nothing bad left to reach. Properties of the form *this must never
  happen* pass trivially against a model with one reachable state: no
  bad state exists to reach. Properties of the other form — *this must
  eventually happen*, the queue drains, the lock is released — do not
  collapse the same way, because a model that sits in one state forever
  never gets there either. So an over-abstracted model tends to go green
  on every must-never check and red on the must-eventually ones. That
  split is the tell.
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
