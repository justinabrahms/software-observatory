---
id: SO-001
title: Type Checker
family: structural
family_num: 1
oracle: maximum
oracle_note: 'a type error is a fact, not an opinion'
independence: maximum
independence_note: 'the implementation cannot game the compiler'
scope: module
latency: milliseconds
actionability: guiding
actionability_note: 'tells you exactly what''s wrong and where'
type: predictive
type_note: 'catches errors before runtime'
stack_level: static-analysis
categories:
- Structural
- Syntactic Validity
- Guiding Sensors
- Maximum Oracle
see_also:
- SO-003
- SO-001b
- SO-004
- atlas
last_reviewed: 2026-08-23
references:
- title: 'To Type or Not to Type: Quantifying Detectable Bugs in JavaScript'
  year: 2017
  tier: I
  url: https://www.microsoft.com/en-us/research/wp-content/uploads/2017/09/gao2017javascript.pdf
  kind: paper
- title: Eliminating Memory Safety Vulnerabilities at the Source
  year: 2024
  tier: II
  url: https://security.googleblog.com/2024/09/eliminating-memory-safety-vulnerabilities-Android.html
  kind: paper
- authors: Luca Cardelli
  title: Type Systems
  year: 2004
  kind: paper
- title: Rust compiler
  kind: tool
  url: https://www.rust-lang.org
- title: TypeScript
  kind: tool
  url: https://www.typescriptlang.org
- title: Mypy
  kind: tool
  url: https://mypy-lang.org
- title: pyright
  kind: tool
  url: https://github.com/microsoft/pyright
---

A Rust compiler saying `expected Option<Foo>, found Foo` is vastly more useful
to an agent than "please reconsider whether this is correct." This is the
first and strongest form of computational feedback in Böckeler's guides &
sensors framing. The implementation doesn't get to argue with it.

## Sensors of syntactic validity

The type checker is the strongest member of the cheapest family of sensors
— those that answer: *"Is this thing even a valid inhabitant of the
language/system?"*

```
compiler         → "does it parse and compile?"
type checker     → "are types consistent?"
schema validator → "is this a valid instance of the schema?"
import resolver  → "do all imports resolve?"
dependency resolver → "are all dependencies available?"
```

These are extremely strong sensors because the implementation doesn't get to
argue with them. A type error is not a suggestion — it is a fact about the
artifact. This makes them the baseline of the [confidence stack](atlas.html).

> A guiding sensor tells the agent what to do next. `expected Option<Foo>,
> found Foo` doesn't just say "bad" — it says "you have an `Option` where you
> need a bare `Foo`, probably unwrap it or change the return type." That's
> actionability.

## In practice

A type-checker reading is a diagnostic naming both sides of a
mismatch, which is what makes it actionable rather than merely
negative:

```
checkout.py:87: error: Argument 1 to "apply_discount" has
  incompatible type "float"; expected "Decimal"  [arg-type]
Found 1 error in 1 file (checked 214 source files)
```

In a gradual type system the reading is only as strong as the checked
surface: mypy over an `Any`-riddled codebase, or `tsc` with
`strict: false`, reports a subset of the truth. Read the diagnostic
together with the coverage of the checker itself. And when the
message names two types that look identical, suspect two distinct
types with the same name from different modules, or a generic
parameter that failed to unify. The checker is precise about this;
the reader usually is not.

## Response playbook

When the checker fires, the response is a decision, not a reflex:

1. **Fix at the source of the mismatch, not at its symptom.** If a
   wrong value propagated through five call sites, correcting the
   producer deletes all five errors at once.
2. **If the type is wrong, change the type; if the code is wrong,
   change the code.** Both are legitimate. Guessing which without
   checking the intent is how type errors get "fixed" by casts.
3. **Reach for a cast or `ignore` only after the first two fail,**
   and treat each one as a reviewable artifact. A cast is the
   author asserting the checker lacks information it actually has.
4. **Tighten the checker after every real catch.** A bug the checker
   missed is an argument for a stricter mode or a narrower type, not
   for moving on.

## What it cannot detect

Types measure a particular class of *structural inconsistency*. They cannot
detect *logical errors* — a function that type-checks perfectly but returns
the wrong answer. They cannot detect *runtime behavior*. They cannot tell
you whether the system produces the *intended result for users*.
