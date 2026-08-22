---
id: SO-011c
title: Producer-Evaluator Separation
family: ai-sensors
family_num: "11"
oracle: high
independence: maximum
scope: system
latency: varies
actionability: guiding
type: predictive
stack_level: behavioral-tests
categories:
  - AI-Generated
  - Independence
  - Agent Safety
see_also:
  - SO-011
  - SO-011b
  - SO-011d
  - SO-003
---

A model writing `tests/` is allowed to write tests that make itself pass.
The producer and evaluator should be separated wherever possible.

## The core problem

When an agent writes both the code and the tests, the tests have low
[independence](framework.html). The agent can write tests that pass on its
implementation regardless of correctness. This is the fundamental weakness of
[example-based tests](example-based-tests.html) and [line
coverage](line-coverage.html) when applied to AI-generated code.

## Solutions

- **Separate authors**: human writes tests, agent writes code
- **Separate models**: different agents write code and tests
- **Use independence-strong sensors**: [mutation testing](mutation-testing.html)
  and [fuzzing](fuzzing.html) have higher independence because the *sensor
  itself* generates the adversarial input, not the code author

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — independence violation is a risk |
| Independence | Maximum — the concept *is* independence |
| Scope | System-level |
| Feedback latency | Varies |
| Actionability | Guiding — identifies where independence is violated |
| Type | Predictive |

## What it cannot detect

Producer-evaluator separation is a principle, not a sensor itself. It must
be operationalized through specific sensors that have structural independence
built in.
