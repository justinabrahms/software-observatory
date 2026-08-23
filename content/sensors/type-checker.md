---
id: SO-001
title: Type Checker
family: structural
family_num: 1
oracle: maximum
independence: maximum
scope: module
latency: milliseconds
actionability: guiding
type: predictive
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
  url: ''
- title: TypeScript
  kind: tool
  url: ''
- title: Mypy
  kind: tool
  url: ''
- title: pyright
  kind: tool
  url: ''
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

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Maximum — a type error is a fact, not an opinion |
| Independence | Maximum — the implementation cannot game the compiler |
| Scope | Module-level |
| Feedback latency | Milliseconds |
| Actionability | Guiding — tells you exactly what's wrong and where |
| Type | Predictive — catches errors before runtime |

## What it cannot detect

Types measure a particular class of *structural inconsistency*. They cannot
detect *logical errors* — a function that type-checks perfectly but returns
the wrong answer. They cannot detect *runtime behavior*. They cannot tell
you whether the system produces the *intended result for users*.
