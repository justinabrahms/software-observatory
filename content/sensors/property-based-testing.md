---
id: SO-005e
title: Property-Based Testing
family: adversarial
family_num: '05'
oracle: high
oracle_note: a property violation is definitive
independence: high
independence_note: the generator is independent of the implementation
scope: function
scope_note: typically function to module
latency: seconds
actionability: guiding
actionability_note: provides the shrunk counterexample
type: predictive
type_note: the generator actively searches for falsifying inputs
stack_level: property-metamorphic
categories:
- Adversarial
see_also:
- SO-005
- SO-005b
- SO-003
- SO-002b
- adversarial
last_reviewed: '2026-08-31'
references:
- title: 'An Empirical Evaluation of Property-Based Testing in Python'
  year: 2025
  tier: I
  url: https://cseweb.ucsd.edu/~mcoblenz/assets/pdf/OOPSLA_2025_PBT.pdf
  kind: publication
  authors: Savitha Ravi, Michael Coblenz
  venue: Proc. ACM Program. Lang. (OOPSLA2)
- title: 'QuickCheck: A Lightweight Tool for Random Testing of Haskell Programs'
  year: 2000
  tier: I
  url: https://www.cs.tufts.edu/~nr/cs257/archive/john-hughes/quick.pdf
  kind: publication
  authors: Koen Claessen, John Hughes
  venue: ACM SIGPLAN Notices
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

You state a property that should hold for *every* input, and the tool
generates inputs trying to break it. Where [example-based
testing](example-based-tests.html) checks one case you thought of,
property-based testing searches the space of cases you didn't.

## Properties vs examples

A property is a universal statement. Here it is stated against a
`my_sort` that orders numbers lexicographically — `sorted(xs, key=str)`,
a bug that hides behind any example whose inputs are non-negative single
digits:

```python
@given(st.lists(st.integers()))
def test_sort_is_ordered(xs):
    ys = my_sort(xs)
    assert ys == sorted(ys)
```

The reading is one falsifying input, already shrunk. Hypothesis runs the
property until it fails, reduces the failure, and reports only the
reduced case — never the input that first broke it:

```
xs = [-1, -2]

    @given(st.lists(st.integers()))
    def test_sort_is_ordered(xs):
        ys = my_sort(xs)
>       assert ys == sorted(ys)
E       assert [-1, -2] == [-2, -1]
E         At index 0 diff: -1 != -2
E         Use -v to get more diff
E       Failing test case: test_sort_is_ordered(
E           xs=[-1, -2],
E       )
```

Two elements and a minus sign, verifiable by hand in seconds: that
reduction is the actionable part of the sensor, and it is invisible in
the output: the larger inputs that also failed are never printed. (The
banner is version-dependent — Hypothesis 6 prints
`Failing test case:` where older releases printed `Falsifying
example:` — so grep for the parameter line, not the banner.)

## How it differs from metamorphic testing

Property-based testing and [metamorphic testing](metamorphic-testing.html)
are siblings in the adversarial family. Property-based testing states a
property directly (`f(x) == f(-x)`, `sort(sort(xs)) == sort(xs)`) and
relies on the generator to find an `x` that breaks it. Metamorphic
testing states a *relation between outputs* — you don't know the
answer, only how the answer should change when the input changes. In
practice most property-based test suites contain metamorphic relations
(idempotence, commutativity, round-trip) and the distinction is mostly
about whether you can name the property outright or only the relation
between two calls.

## How it gets gamed

- **Weaken the property.** Replacing equality with "same length," or
  adding `assume` filters that discard failing inputs, makes the
  property hold while detecting less. The test still runs.
- **Shrink the campaign.** Cutting the example count until failures
  stop appearing keeps the sensor's name and discards its reach.
- **Label violations as flaky.** A property that fails on one input in
  a thousand is failing; retrying until it passes converts a finding
  into noise.

The meta-signal is the ratio of discarded (assumed-away) examples to
generated ones. As it climbs, the property is being strangled.

## Response playbook

When a property fails:

1. **Work from the shrunk example.** The minimized input is the one a
   human can verify by hand in seconds. If you can't hand-check it,
   shrink further before debugging.
2. **Decide which side is wrong.** Usually the implementation.
   Occasionally the property overclaims, and the fix is a corrected
   property, written with the reason, not a deleted test.
3. **Fix the implementation and re-run the campaign.** A property
   violation is rarely one input wide; the same bug usually breaks a
   neighborhood.
4. **Pin the counterexample as a regression test.** The shrunk input
   is a free [example-based test](example-based-tests.html) that runs
   in milliseconds and guards the fix forever.

## What it cannot detect

Property-based testing can only check properties you *state*. If a
function has no obvious property, the generator has nothing to falsify.
It also cannot detect [missing behavior](mutation-testing.html) — if a
feature is absent, there's no property to check against it. And unlike
[fuzzing](fuzzing.html), it assumes you can characterize correctness;
fuzzing finds crashes even when you can't write down a property.
