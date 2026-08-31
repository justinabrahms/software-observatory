---
id: SO-013
title: Statically Checked Invariants
family: invariants
family_num: '04'
oracle: high
oracle_note: a discharged proof obligation is definitive for its claim
independence: high
independence_note: the prover is outside the code
scope: module
latency: milliseconds
latency_note: milliseconds to minutes
actionability: blocking
actionability_note: the build fails
type: predictive
stack_level: static-analysis
categories:
- Invariants
see_also:
- SO-004
- SO-012
- SO-001d
- SO-017
references:
- title: How Amazon Web Services Uses Formal Methods
  year: 2015
  tier: III
  url: https://cacm.acm.org/research/how-amazon-web-services-uses-formal-methods/
  kind: publication
  authors: Chris Newcombe, Tim Rath, Fan Zhang, Bogdan Munteanu, Marc Brooker, Michael Deardeuff
  venue: Communications of the ACM 58(4)
- authors: Leino
  title: Dafny
  year: 2010
  kind: publication
  url: ''
  description: Verification-aware programming language
  tier: IV
- title: Liquid Haskell
  url: https://ucsd-progsys.github.io/liquidhaskell/
  kind: tool
  description: Haskell refinement type checking
- title: Dafny user guide, verification debugging
  url: https://dafny.org/latest/DafnyRef/DafnyRef#sec-counterexamples
  kind: other
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
raised against a property of the program instead of a type. Liquid
Haskell prints the refinement it could infer next to the one the
signature demanded:

```
**** LIQUID: UNSAFE ************************************************************

src/Queue.hs:23:34: error:
    Liquid Type Mismatch
    .
    The inferred type
      VV : {v : GHC.Types.Int | v == size q - 1}
    .
    is not a subtype of the required type
      VV : {VV : GHC.Types.Int | VV >= 0}
    .
    in the context
      q : Queue a
   |
23 |   dequeue q = Q (tail (elems q)) (size q - 1)
   |                                   ^^^^^^^^^^
```

Or, at the type level: a compiler that refuses `head []` because the
list's type carries a proof of non-emptiness. Either way the verdict
arrives at build time, once, for all possible executions.

The two refinements are the reading, and the gap between them is the
finding: `size q - 1` is what the code establishes, `>= 0` is what was
claimed, and nothing rules out `size q == 0`. Note what is *not* in the
message — no failing input, no execution. An SMT-backed checker reports
an unsatisfiable constraint, not a witness. Where a witness can be had at
all it is a side feature and a weak one: Liquid Haskell's
`--counter-examples` is flagged experimental, and Dafny's
`--extract-counterexample` ships with the warning that it "cannot
guarantee that the counterexample it reports provably violates the
assertion", and should be "treated as a hint". Solver models are not
minimal and are often unreachable. An invariant that is right but
unprovable without a helper lemma produces the same message as one the
code genuinely breaks, so the triage question is "which of my two claims
is false?" not "how do I make the message stop."

## Response playbook

When an invariant fails to discharge:

1. **Read the inferred and required refinements against each other
   first.** The gap between what the code establishes and what the
   signature demanded settles most triage in one look, and it is there
   in every message — unlike a counter-example, which most of these
   checkers will not give you.
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
