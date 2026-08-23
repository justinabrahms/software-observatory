---
id: SO-005
title: Fuzzing
family: adversarial
family_num: 05
oracle: high
independence: high
scope: function
latency: minutes-hours
actionability: guiding
type: adversarial
stack_level: property-metamorphic
categories:
  - Adversarial
  - Robustness
  - Input Space
  - Guiding Sensors
see_also:
  - SO-005b
  - SO-003
  - adversarial
last_reviewed: 2026-08-23
---

What happens on inputs humans didn't think of? Fuzzing is a sensor of
*robustness* against the infinite space of inputs the system will actually
encounter — including inputs no engineer would ever write deliberately.

## The oracle question

Property-based testing asks: "does the implementation obey generalized
properties across huge input spaces?" Fuzzing asks a simpler question: "does
it crash?" The oracle is cheap — panics, exceptions, assertions, memory
violations — but the coverage of input space is enormous.

```
# Coverage-guided fuzzing
1. Generate random or mutated input
2. Feed it to the system
3. Did new code paths execute?
   Yes → keep this input, mutate further
   No  → discard, try again
4. Did the system crash, panic, or violate an assertion?
   Yes → save the input as a finding
   No  → continue
```

> Fuzzing is particularly powerful because it explores the input space that
> humans systematically under-sample. An engineer writes tests for inputs
> they can imagine. A fuzzer discovers inputs they can't.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High for crashes, lower for correctness |
| Independence | High — inputs are generated independently of the implementation |
| Scope | Function-level (usually) |
| Feedback latency | Minutes to hours |
| Actionability | Guiding — provides the exact input that triggers the failure |
| Type | Adversarial — actively tries to break the system |

## What it cannot detect

Fuzzing with a crash oracle cannot detect *wrong but non-crashing* behavior.
A function that returns the wrong answer without crashing will pass a fuzzer.
For correctness properties, pair fuzzing with [property-based
testing](metamorphic-testing.html) or [mutation testing](mutation-testing.html).

## Tooling

- libFuzzer
- cargo-fuzz
- AFL++
- CIFuzz

## References

- Evaluating Fuzz Testing (2018, tier I) — https://dl.acm.org/doi/10.1145/3243734.3243804
- An Empirical Study of OSS-Fuzz Bugs (2021, tier II) — https://arxiv.org/pdf/2103.11518

- Manes et al., 'The Art, Science, and Engineering of Fuzzing: A Survey' (2021)
- libFuzzer: https://llvm.org/docs/LibFuzzer.html