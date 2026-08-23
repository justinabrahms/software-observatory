---
id: SO-008b
title: Architecture Fitness Functions
family: architecture
family_num: "08"
oracle: high
independence: high
scope: system
latency: seconds
actionability: guiding
type: predictive
stack_level: static-analysis
categories:
  - Architecture
  - Boundary Sensors
  - Guiding Sensors
see_also:
  - SO-008
  - SO-008c
  - SO-008d
last_reviewed: 2026-08-23
---

`frontend -> application -> domain -> infrastructure`, and fail if `domain
-> infrastructure`. A sensor of *architectural drift*.

Architecture fitness functions are executable assertions about the structure
of the code. They fail when the architecture violates a rule: a domain layer
importing infrastructure, a service bypassing its API, a forbidden
dependency forming. They turn architectural rules from prose into
[computational gates](catalog.html#ai-sensors).

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — a violation is definitive |
| Independence | High — rules are external to the code |
| Scope | System-level |
| Feedback latency | Seconds |
| Actionability | Guiding — shows which rule was violated and where |
| Type | Predictive |

## What it cannot detect

Fitness functions only check rules you've *codified*. Implicit architectural
rules that haven't been expressed as functions are invisible to this sensor.

## Tooling

- ArchUnit
- NetArchTest
- dependency-cruiser

## References

- ArchUnit: https://www.archunit.org
