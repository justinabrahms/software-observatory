---
id: SO-017
title: Theorem Proving
family: structural
family_num: '01'
oracle: maximum
oracle_note: a machine-checked proof is the strongest oracle there is
independence: medium
independence_note: the human writes the proof; the checker verifies it
scope: module
scope_note: the proof target, not the surrounding system
latency: hours
latency_note: hours to weeks for non-trivial targets
actionability: blocking
actionability_note: an unproved goal stops the build
type: predictive
stack_level: static-analysis
categories:
- Structural
- Formal Methods
see_also:
- SO-012
- SO-013
- SO-016
- SO-001
- structural
last_reviewed: '2026-08-24'
references:
- title: 'seL4: Formal Verification of an OS Kernel'
  year: 2009
  tier: III
  url: https://trustworthy.systems/publications/nicta_full_text/1852.pdf
  kind: publication
  authors: Gerwin Klein, Kevin Elphinstone, Gernot Heiser, June Andronick, David Cock,
    Philip Derrin, Dhammika Elkaduwe, Kai Engelhardt, Rafal Kolanski, Michael Norrish,
    Thomas Sewell, Harvey Tuch, Simon Winwood
  venue: SOSP 2009
- title: Formal verification of a realistic compiler
  year: 2009
  tier: III
  url: https://xavierleroy.org/publi/compcert-CACM.pdf
  kind: publication
  authors: Xavier Leroy
  venue: Communications of the ACM 52(7)
- title: 'Certified Programming with Dependent Types'
  year: 2013
  tier: IV
  url: https://adam.chlipala.net/cpdt/
  kind: publication
  authors: Adam Chlipala
  description: A textbook on Coq and machine-checked proof
- title: Coq
  url: https://coq.inria.fr
  kind: tool
  description: Proof assistant for constructive mathematics
- title: Lean
  url: https://leanprover.github.io
  kind: tool
  description: Theorem prover and programming language
- title: Isabelle/HOL
  url: https://isabelle.in.tum.de
  kind: tool
  description: Generic proof assistant
- title: Frama-C WP
  url: https://frama-c.com
  kind: tool
  description: Weakest-precondition calculus plugin for C verification
---

A machine-checked proof that a property holds for all inputs, not just the
ones a test happened to exercise. Where [contract & refinement types](contract-refinement-types.html)
ask the compiler to discharge obligations automatically, theorem proving
has a human write the proof and a checker verify it — the strongest oracle
in the catalog, at the cost of the most human effort of any sensor here.

The distinction from [model checking](model-checking.html) is the proof
strategy: model checking exhausts a finite state space; theorem proving
constructs a general argument that holds for all inputs, bounded or not.
The distinction from [statically checked invariants](statically-checked-invariants.html)
is the automation: Dafny and Liquid Haskell try to discharge obligations
without human guidance; Coq, Lean, and Isabelle require the human to write
the proof script, and the checker verifies each step. The human is the
prover; the machine is the auditor.

## In practice

A reading is a proof state — the goal the checker cannot close, with the
context the human left it in:

```
1 subgoal
H : n <= m
IHn : forall k, k <= n -> k + 1 <= m + 1
====================================
n + 1 <= m + 1
```

The `====================================` is the obligation the checker cannot
discharge from the hypotheses above it. Unlike a test failure, the verdict
is not "this case broke" but "this step of the argument is missing." The
fix is almost always a lemma the human forgot to state, or an induction
hypothesis applied at the wrong type. The checker is never wrong about
whether a step closes; it is only silent about which step to try next.

## Response playbook

When a proof goal fails to close:

1. **Read the goal and the hypotheses.** The gap between them is the
   missing step. The checker prints exactly what it knows and what it
   needs; the human's job is to see the bridge.
2. **Try the obvious induction first.** Most failed goals are missing
   an induction hypothesis applied at a stronger type than the human
   stated.
3. **If the goal is unprovable, the spec is wrong.** A goal that cannot
   close after sustained effort is evidence the property is false, not
   that the prover is weak. Extract the counter-example and treat it as
   a failing test.
4. **If the goal is provable but the proof is too long, state lemmas.**
   A proof script that sprawls is a sign the argument is missing
   structure; lemmas are how proofs get smaller.

## How it gets gamed

The checker cannot be gamed, but the proof can be degraded:

- **`admit` and `sorry`.** Every proof assistant has an escape hatch that
  discharges any goal with "trust me." A proof that compiles with
  `admit` in it is not a proof; it is a claim. The count of `admit`s is
  the meta-signal.
- **Axioms that shouldn't be axioms.** Declaring a property as an axiom
  discharges it without proof. An axiom that is actually a theorem is
  a proof obligation the author skipped.
- **Proofs of the wrong property.** The spec is written by the same
  mind that writes the code, so a proof of a trivial restatement of
  the implementation is a proof that protects nothing. The spec's
  strength is the meta-signal: does the proven property say what the
  system needs to be true, or does it say what the code already does?
- **Verification off the merge path.** A proof that runs nightly or on
  demand, rather than on every merge, is a proof nobody is waiting for.

The meta-signal is `admit` count and axiom inventory. A proof with zero
`admit`s and no unproven axioms is a proof; a proof with either is a
claim wearing a proof's clothes.

## What it cannot detect

Theorem proving cannot detect that the spec matches the system's actual
requirements. A proof of `forall n, n + 0 = n` is a valid proof of a
trivial property; the checker is satisfied, the system is unprotected.
The gap between "the property holds" and "the property is the one the
business needs" is exactly what [business invariants](business-invariants.html)
measure from the other direction.

Theorem proving also cannot detect properties of the runtime environment
that the proof target abstracts away. A proof that the algorithm is
correct does not prove the allocator won't return `NULL`, the network
won't drop the message, or the operator won't misconfigure the deploy.
Those belong to [runtime invariants](runtime-invariants.html) and
[observability events](observability-events.html).
