---
id: SO-012
title: Contract & Refinement Types
family: structural
family_num: '01'
oracle: high
oracle_note: a proof is the strongest oracle short of running the system
independence: high
independence_note: the checker cannot be gamed by the code it checks
scope: function
latency: milliseconds
actionability: blocking
actionability_note: a failed contract stops the build
type: predictive
stack_level: static-analysis
categories:
- Structural
see_also:
- SO-001
- SO-001d
- SO-002
- SO-005
- structural
last_reviewed: '2026-08-24'
references:
- title: How Amazon Web Services Uses Formal Methods
  year: 2015
  tier: III
  url: https://cacm.acm.org/research/how-amazon-web-services-uses-formal-methods/
  kind: paper
  authors: Chris Newcombe, Tim Rath, Fan Zhang, Bogdan Munteanu, Marc Brooker, Michael Deardeuff
  venue: Communications of the ACM 58(4)
- authors: Leino
  title: 'Dafny: An Automatic Program Verifier'
  year: 2010
  kind: paper
  tier: IV
- title: Dafny
  url: https://dafny.org
  kind: tool
  description: Verification-aware programming language
- title: Frama-C
  kind: tool
  url: https://frama-c.com
  description: Static analysis and verification for C
- title: JML
  kind: tool
  url: https://www.openjml.org
  description: Java Modeling Language for behavioral interface specifications
- title: Rust typestate
  kind: tool
  url: https://docs.rust-embedded.org/book/static-guarantees/typestate-programming.html
  description: Rust's type system encoding program states
---

Behavioral guarantees checked before the code ever runs. Typestate systems,
refinement types, and design-by-contract annotations (Eiffel-style
pre/postconditions, Dafny `requires`/`ensures`) ask the compiler to prove
that certain behaviors are impossible, not merely unlikely.

Where a [type checker](type-checker.html) answers "do the shapes fit?", a
refinement type answers "can `withdraw(amount)` ever be called with
`amount > balance`?" — a behavioral claim, discharged at build time.

## In practice

A contract check reads like a proof obligation returned unpaid. The
diagnostic names the obligation that failed, and usually the related
location where it was stated:

```
Program.dfy(14,4): Error: A precondition for this call could not be
proved on an entry point of this program
Program.dfy(14,17): Related location: This is the precondition that
could not be proved
Program.dfy(9,11): Related location: this is the precondition
```

Three causes produce the same message, and the fix is different for
each: the implementation violates its own contract, the contract is
wrong, or the prover needs an intermediate lemma to connect the two.
The message alone does not say which. Unlike a test failure, though,
the verdict is deterministic: a contract that fails today fails on
every machine, and a proof that discharges never flakes. The counter-
examples some checkers print are worth keeping; they are the minimal
inputs that break the claim.

## Response playbook

When a contract fails to discharge:

1. **Reproduce with the smallest failing input.** If the checker
   emits a counter-example, run it; if not, derive one from the
   failed obligation.
2. **Decide whether the implementation or the contract is wrong.**
   A failed proof is a genuine disagreement between two claims the
   author made, and one of them must be retracted.
3. **If both are right, supply the missing lemma.** Splitting the
   obligation into smaller steps is how proofs go through; deleting
   the contract is how they get abandoned.
4. **Demote what cannot be proved.** An obligation that resists the
   prover can still ship as a
   [runtime invariant](runtime-invariants.html), checked on every
   execution instead of all executions.

## How it gets gamed

The checker cannot be gamed, but the contracts are written by the
same mind that writes the code, so the specification itself can be
degraded:

- **Trivial contracts.** `ensures true`, postconditions that restate
  the type signature. The checker passes and protects nothing.
- **Weaken until green.** Each fight loosens the precondition one
  notch until the proof goes through by erosion rather than by
  correctness.
- **Verification off the merge path.** A proof job that runs nightly
  or on demand, rather than on every merge, is a proof nobody is
  waiting for.

The meta-signal is contract strength: sample annotated functions and
count how many have postconditions that are trivially true.

## What it cannot detect

Contracts only cover what was specified. The specification itself is
written by the same mind that wrote the code, which is why contract checking
composes with rather than replaces [example-based tests](example-based-tests.html)
and [property testing](fuzzing.html).
