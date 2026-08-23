---
id: SO-007c
title: API Compatibility
family: change
family_num: "07"
oracle: high
independence: high
scope: service
latency: seconds
actionability: guiding
type: predictive
stack_level: integration-tests
categories:
  - Change
  - Boundary Assumptions
see_also:
  - SO-002
  - SO-007
  - SO-007d
last_reviewed: 2026-08-23
---

Did externally observable contracts change? A sensor of *boundary stability*
— can old and new versions coexist?

API compatibility checking verifies that a change doesn't break existing
consumers. This is the [contract test](contract-tests.html) applied to
change: not "does the contract hold now" but "did the contract change
between versions."

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — breaking changes are definitive |
| Independence | High — schema/contract is external |
| Scope | Service-level |
| Feedback latency | Seconds |
| Actionability | Guiding — shows which API surface changed |
| Type | Predictive |

## What it cannot detect

API compatibility checks the *shape* of the interface, not the
*behavioral meaning*. A response with the same fields and types but
different semantics will pass compatibility checks.
