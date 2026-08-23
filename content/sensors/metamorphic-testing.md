---
id: SO-005b
title: Metamorphic Testing
family: adversarial
family_num: 5
oracle: high
independence: high
scope: function
latency: minutes
actionability: guiding
type: adversarial
stack_level: property-metamorphic
categories:
- Adversarial
- Oracle-Free
- Metamorphic Relations
- Guiding Sensors
see_also:
- SO-005
- SO-003
- adversarial
- invariants
last_reviewed: 2026-08-23
references:
- title: An Empirical Evaluation of Property-Based Testing in Python
  year: 2025
  tier: I
  url: https://cseweb.ucsd.edu/~mcoblenz/assets/pdf/OOPSLA_2025_PBT.pdf
  kind: paper
- authors: Chen et al.
  title: 'Metamorphic Testing: A New Approach for Generating Next Test Cases'
  year: 1998
  kind: paper
- title: Hypothesis
  url: https://hypothesis.readthedocs.io
  kind: tool
  description: Property-based testing for Python
- title: QuickCheck
  kind: tool
  url: ''
  description: Property-based testing for Haskell
- title: fast-check
  kind: tool
  url: ''
  description: Property-based testing for TypeScript
- title: test.check
  kind: tool
  url: ''
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
sqrt(x) * sqrt(x) == x                 # inverse
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

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — relation violations are definitive |
| Independence | High — relations are independent of implementation |
| Scope | Function-level |
| Feedback latency | Minutes |
| Actionability | Guiding — shows which relation was violated |
| Type | Adversarial — explores input perturbations |

## What it cannot detect

Metamorphic testing can only check relations you *know*. If a function has
no obvious metamorphic relations, this sensor has nothing to test. It also
cannot detect [missing behavior](mutation-testing.html) — if a feature is
absent, there's no function to check relations on.
