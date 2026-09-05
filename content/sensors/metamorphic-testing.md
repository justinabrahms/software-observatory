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
- SO-005e
- adversarial
- invariants
last_reviewed: '2026-08-31'
references:
- title: An Empirical Evaluation of Property-Based Testing in Python
  year: 2025
  tier: I
  url: https://cseweb.ucsd.edu/~mcoblenz/assets/pdf/OOPSLA_2025_PBT.pdf
  kind: publication
  authors: Savitha Ravi, Michael Coblenz
  venue: Proc. ACM Program. Lang. (OOPSLA2)
- authors: Chen et al.
  title: 'Metamorphic Testing: A New Approach for Generating Next Test Cases'
  year: 1998
  kind: publication
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
sort(sort(x))       == sort(x)         # idempotence
decrypt(encrypt(x)) == x               # round-trip
sort(x) == sort(shuffle(x))            # order-independence

# Numeric examples:
abs(x) == abs(-x)                      # sign-independence
abs(x + y) <= abs(x) + abs(y)          # triangle inequality
max(x, y) == max(y, x)                 # commutativity
```

You don't need to know what `sort(x)` returns. You just need to know that
`sort(sort(x))` should equal `sort(x)`. If it doesn't, something is wrong —
and you've found a bug without ever needing to compute the correct answer.

> Metamorphic testing is the answer to "how do you test something when you
> can't compute the expected output?" Fuzzing explores the input space.
> Mutation testing perturbs the implementation. Metamorphic testing perturbs
> the input and checks relations between outputs. All three are adversarial
> — all three try to make the system fail.

The boundary with [property-based testing](property-based-testing.html)
is what the assertion is about. A property is a claim about one output:
`sorted(ys) == ys`. A relation is a claim about two outputs from two
related inputs, and needs an answer key for neither. The same generator
drives both, most property-based suites contain both, and the difference
shows up when the property is not statable: nobody can write down what a
route planner should return, but `route(a, b)` and `route(b, a)` should
cost the same.

## In practice

A reading is a relation violation, already reduced. The relation below
is order-independence — sorting a list and sorting its reverse must
agree, which is checkable without knowing what the sorted answer is —
run against a `my_sort` that makes one bubble pass instead of a full
sort:

```
xs = [0, 0, -1]

    @given(st.lists(st.integers()))
    def test_sort_is_order_independent(xs):
>       assert my_sort(xs) == my_sort(list(reversed(xs)))
E       assert [0, -1, 0] == [-1, 0, 0]
E         At index 0 diff: 0 != -1
E         Use -v to get more diff
E       Failing test case: test_sort_is_order_independent(
E           xs=[0, 0, -1],
E       )
```

Reading it well:

1. **The named relation is the oracle.** The failure says which
   relation broke (idempotence, round-trip, commutativity), which
   tells you what kind of bug to look for before you look at the
   code.
2. **The printed case is already the shrunk one.** Hypothesis reports
   the reduced input and nothing else; the larger inputs that also
   failed never reach the console. If the printed case is still too
   big to hand-check, the shrinker was blocked — usually by an
   `assume` filter or a test that is not deterministic.
3. **A relation that never fails deserves a glance.** It may be a
   strong invariant, or it may be vacuous. Check that it would have
   fired on a known-bad version of the code.

## How it gets gamed

The relation is chosen by the same people who wrote the code, and a
relation can be true of almost any implementation:

- **Pick a relation the bug cannot break.** `len(sort(x)) == len(x)`
  holds for a function that returns its input untouched. A relation
  that cannot tell the real sort from `return x` is a test of the
  harness, and a suite of such relations reports green forever.
- **Read the relation off the implementation.** Writing down what the
  code happens to preserve, instead of what the function is for, turns
  the relation into a restatement of the code. It will fail only when
  the code changes, which is a snapshot test with extra steps.
- **Starve the source inputs.** The relation is checked on `x` and on
  a transform of `x`. If the generator for `x` never produces empty
  lists, duplicates or negatives, both sides are computed on inputs
  where the bug never fires, and the transform inherits the gap.
- **Filter the follow-up.** An `assume` clause that discards
  transformed inputs which "do not apply" is where violations go to
  disappear, one excluded case at a time.

The meta-signal is whether each relation has a recorded kill: a
version of the code it has been seen to fail against. A relation with
no kill on record has not yet been shown to be an oracle.

## Response playbook

When a relation is violated:

1. **Run both sides by hand on the shrunk input.** A violation has two
   computations in it, and the first question is which one is wrong.
   In the reading above, `my_sort([0, 0, -1])` returning `[0, -1, 0]`
   is wrong on its own; the reversed run is only the witness.
2. **Check whether the relation overclaims.** Round-trips fail on
   lossy encodings and commutativity fails on floating point. When the
   relation is the bug, correct it and record why; a deleted relation
   is a deleted sensor.
3. **Pin the pair.** Both inputs and both outputs go into an
   [example-based test](example-based-tests.html), so the fix is
   guarded without re-running the campaign.
4. **Re-run the relation's siblings.** A sort that fails
   order-independence usually fails idempotence too. Run the whole
   relation set against the fix, not only the one that fired.

## What it cannot detect

Metamorphic testing can only check relations you *know*. If a function has
no obvious metamorphic relations, this sensor has nothing to test. It also
cannot detect [missing behavior](mutation-testing.html) — if a feature is
absent, there's no function to check relations on.
