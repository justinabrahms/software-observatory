---
id: SO-013
title: Statically Checked Invariants
family: invariants
family_num: '04'
oracle: high
oracle_note: 'a discharged proof obligation is definitive for its claim'
independence: high
independence_note: 'the prover is outside the code'
scope: module
latency: milliseconds
latency_note: 'milliseconds to minutes'
actionability: blocking
actionability_note: 'the build fails'
type: predictive
stack_level: static-analysis
categories:
- Invariants
- Formal Methods
see_also:
- SO-004
- SO-012
- SO-001d
last_reviewed: 2026-08-23
references:
- title: How Amazon Web Services Uses Formal Methods
  year: 2015
  tier: III
  url: https://cacm.acm.org/research/how-amazon-web-services-uses-formal-methods/
  kind: paper
- authors: Leino
  title: Dafny
  year: 2010
  kind: paper
  url: ''
  description: Verification-aware programming language
- title: Liquid Haskell
  url: https://ucsd-progsys.github.io/liquidhaskell/
  kind: tool
  description: Haskell refinement type checking
- title: Frama-C
  kind: tool
  url: https://frama-c.com
  description: Static analysis and verification for C
- title: JML
  kind: tool
  url: https://www.openjml.org
  description: Java Modeling Language for behavioral interface specifications
---

Invariants the compiler refuses to let you violate: Dafny `invariant`
clauses, Frama-C annotations, JML specs, type-level witnesses like
`NonEmptyList`. Where [database invariants](database-invariants.html) are
checked by a live system against live data, these are proved once, at build
time, for all possible executions.

## In practice

The reading is the same as a [type-checker](type-checker.html) error,
raised against a property of the program instead of a type:

```
src/Queue.hs:23:1: Error: Liquid Type Mismatch
  Invariant `size q >= 0` could not be proved
  Counter-example: `q` after `dequeue (mkQueue [])`
```

Or, at the type level: a compiler that refuses `head []` because the
list's type carries a proof of non-emptiness. Either way the verdict
arrives at build time, once, for all possible executions, and a
counter-example when the checker can find one.

The counter-example is the part to read first: it is the smallest
state that violates the invariant, and it usually says immediately
whether the invariant is wrong or the code is. An invariant that is
right but unprovable without a helper lemma produces the same message
as one the code genuinely breaks, so the triage question is "which of
my two claims is false?" not "how do I make the message stop."

## Response playbook

When an invariant fails to discharge:

1. **Read the counter-example first.** It is the minimal violating
   state, and it settles most triage in one look.
2. **If the code is wrong, fix the code; if the invariant is wrong,
   fix the statement.** A proof of the wrong invariant is worse than
   no proof, because it creates false confidence.
3. **If both are right, supply the lemma.** Proofs that fail for lack
   of an intermediate step go through once the step is written down.
4. **Demote only what cannot be proved.** An invariant that resists
   the prover can still run as a
   [runtime invariant](runtime-invariants.html) on every execution,
   and it should.

## What it cannot detect

Invariants that were never written down, and invariants whose statement is
wrong. The gap between "the invariant holds" and "the invariant is the one
the business needs" is exactly what [business invariants](business-invariants.html)
measure from the other direction.
