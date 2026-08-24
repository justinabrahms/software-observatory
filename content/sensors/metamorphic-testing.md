---
id: SO-005b
title: Metamorphic Testing
family: adversarial
family_num: 5
oracle: high
oracle_note: relation violations are definitive
independence: high
independence_note: relations are independent of implementation
scope: function
latency: minutes
actionability: guiding
actionability_note: shows which relation was violated
type: predictive
type_note: explores input perturbations
stack_level: property-metamorphic
categories:
- Adversarial
- Oracle-Free
see_also:
- SO-005
- SO-003
- adversarial
- invariants
last_reviewed: '2026-08-24'
references:
- title: An Empirical Evaluation of Property-Based Testing in Python
  year: 2025
  tier: I
  url: https://cseweb.ucsd.edu/~mcoblenz/assets/pdf/OOPSLA_2025_PBT.pdf
  kind: paper
  authors: Savitha Ravi, Michael Coblenz
  venue: Proc. ACM Program. Lang. (OOPSLA2)
- authors: Chen et al.
  title: 'Metamorphic Testing: A New Approach for Generating Next Test Cases'
  year: 1998
  kind: paper
  tier: IV
- title: Hypothesis
  url: https://hypothesis.readthedocs.io
  kind: tool
  description: Property-based testing for Python
- title: QuickCheck
  kind: tool
  url: https://hackage.haskell.org/package/QuickCheck
  description: Property-based testing for Haskell
- title: fast-check
  kind: tool
  url: https://fast-check.dev
  description: Property-based testing for TypeScript
- title: test.check
  kind: tool
  url: https://github.com/clojure/test.check
  description: Property-based testing for Clojure
---

You don't know the answer, but you know *how the answer should change*. This
is a particularly beautiful sensor because you don't need an oracle.

## Metamorphic relations

A metamorphic relation is a statement about how the output of a function
should change when the input changes in a specific way:

```
sort(sort(x))      == sort(x)          # idempotence
encrypt(decrypt(x)) == x              # round-trip
f(x) == f(shuffle(x))                 # order-independence

# Numeric examples:
abs(x) == abs(-x)                     # sign-independence
abs(x) + abs(y) == abs(x + y)          # triangle inequality
max(x, y) == max(y, x)                # commutativity
```

You don't need to know what `sort(x)` returns. You just need to know that
`sort(sort(x))` should equal `sort(x)`. If it doesn't, something is wrong —
and you've found a bug without ever needing to compute the correct answer.

> Metamorphic testing is the answer to "how do you test something when you
> can't compute the expected output?" Fuzzing explores the input space.
> Mutation testing perturbs the implementation. Metamorphic testing perturbs
> the input and checks relations between outputs. All three are adversarial
> — all three try to make the system fail.

## In practice

A reading is a relation violation, shrunk to the smallest input that
breaks it:

```
______________ test_sort_is_idempotent ______________

Falsifying example:
    x = [2, 1, 3]

assert sort(sort(x)) == sort(x)
AssertionError: [1, 2, 3] != [1, 3, 2]

Shrunk to minimal failing input: x = [2, 1]
```

Reading it well:

1. **The named relation is the oracle.** The failure says which
   relation broke (idempotence, round-trip, commutativity), which
   tells you what kind of bug to look for before you look at the
   code.
2. **Work from the shrunk example.** The original random input is
   noise; the minimized case is the one you can verify by hand in
   seconds. If you cannot hand-check it, shrink further.
3. **A relation that never fails deserves a glance.** It may be a
   strong invariant, or it may be vacuous. Check that it would have
   fired on a known-bad version of the code.

## How it gets gamed

- **Weaken the relation.** Replacing equality with "same length," or
  adding assumption filters, makes violations disappear by narrowing
  what the relation claims. The test still runs and now detects
  less.
- **Shrink the campaign.** Cutting the example count until failures
  stop appearing keeps the sensor's name and discards its reach.
- **Label violations as flaky.** A relation that fails on one input
  in a thousand is failing; retrying until it passes converts a
  finding into noise.

The meta-signal is the ratio of discarded (assumed-away) examples to
generated ones. As it climbs, the relation is being strangled.

## Response playbook

When a relation is violated:

1. **Work from the shrunk example.** The minimized input is the one
   a human can verify by hand in seconds. If you cannot hand-check
   it, shrink it further before debugging.
2. **Decide which side of the relation is wrong.** Usually the
   implementation. Occasionally the relation overclaims, and then
   the fix is a corrected relation, written with the reason, not a
   deleted test.
3. **Fix the implementation and re-run the campaign.** A relation
   violation is rarely one input wide; the same bug usually breaks a
   neighborhood.
4. **Pin the counterexample as a regression test.** The shrunk input
   is a free [example-based test](example-based-tests.html) that
   runs in milliseconds and guards the fix forever.

## What it cannot detect

Metamorphic testing can only check relations you *know*. If a function has
no obvious metamorphic relations, this sensor has nothing to test. It also
cannot detect [missing behavior](mutation-testing.html) — if a feature is
absent, there's no function to check relations on.
