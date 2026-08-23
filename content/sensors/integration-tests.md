---
id: SO-002c
title: Integration Tests
family: behavioral
family_num: "02"
oracle: high
independence: low
scope: service
latency: minutes
actionability: guiding
type: predictive
stack_level: integration-tests
categories:
  - Behavioral
  - Integration
see_also:
  - SO-002
  - SO-002b
  - SO-002d
last_reviewed: 2026-08-23
---

Does the thing work when connected to its actual dependencies? Catches
failures that [unit tests](example-based-tests.html) structurally cannot
see — connection failures, serialization mismatches, timeout behavior.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — failure means the integration is broken |
| Independence | Low — same team writes code and tests |
| Scope | Service-level |
| Feedback latency | Minutes |
| Actionability | Guiding — shows which integration point failed |
| Type | Predictive |

## What it cannot detect

Integration tests with mock dependencies don't test the real integration.
They test your assumptions about the real integration. [Contract
tests](contract-tests.html) are a stronger sensor for boundary assumptions.
