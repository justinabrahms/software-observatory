---
id: SO-012
title: Contract & Refinement Types
family: behavioral
family_num: "02"
oracle: high
independence: high
scope: function
latency: milliseconds
actionability: blocking
type: predictive
stack_level: static-analysis
categories:
  - Behavioral
  - Design by Contract
see_also:
  - SO-001d
  - SO-002
  - SO-005
last_reviewed: 2026-08-23
---

Behavioral guarantees checked before the code ever runs. Typestate systems,
refinement types, and design-by-contract annotations (Eiffel-style
pre/postconditions, Dafny `requires`/`ensures`) ask the compiler to prove
that certain behaviors are impossible, not merely unlikely.

Where a [type checker](type-checker.html) answers "do the shapes fit?", a
refinement type answers "can `withdraw(amount)` ever be called with
`amount > balance`?" — a behavioral claim, discharged at build time.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — a proof is the strongest oracle short of running the system |
| Independence | High — the checker cannot be gamed by the code it checks |
| Scope | Function to module |
| Feedback latency | Milliseconds |
| Actionability | Blocking — a failed contract stops the build |
| Type | Predictive |

## What it cannot detect

Contracts only cover what was specified. The specification itself is
written by the same mind that wrote the code, which is why contract checking
composes with rather than replaces [example-based tests](example-based-tests.html)
and [property testing](fuzzing.html).

## Tooling

- Dafny
- Frama-C
- JML
- Rust typestate

## References

- How Amazon Web Services Uses Formal Methods (2015, tier III) — https://cacm.acm.org/research/how-amazon-web-services-uses-formal-methods/

- Leino, 'Dafny: An Automatic Program Verifier' (2010)
- Dafny: https://dafny.org