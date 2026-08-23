---
id: SO-005d
title: Fault Injection
family: adversarial
family_num: "05"
oracle: medium
independence: high
scope: system
latency: minutes
actionability: guiding
type: adversarial
stack_level: canary-shadow
categories:
  - Adversarial
  - Resilience
  - Chaos Engineering
see_also:
  - SO-004
  - SO-005
  - change-family
last_reviewed: 2026-08-23
---

Kill a node. Drop a network connection. Inject latency. A sensor of
*resilience* — does the system continue to satisfy its
[invariants](runtime-invariants.html) under partial failure?

## Chaos as a sensor

Fault injection (chaos engineering) is an adversarial sensor that tests
whether the system's [runtime invariants](runtime-invariants.html) hold
when dependencies fail. It operates at the system level, not the function
level — you're testing the emergent behavior of distributed components
under stress.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — depends on what invariants you check |
| Independence | High — failures are injected externally |
| Scope | System-level |
| Feedback latency | Minutes |
| Actionability | Guiding — shows which invariant broke under which failure |
| Type | Adversarial |

## What it cannot detect

Fault injection can only test failure modes you *thought to inject*. Unknown
failure modes (cascading failures from unexpected coupling) require
[observability](observability-events.html) to detect in production.
