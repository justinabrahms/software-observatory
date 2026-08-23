---
id: SO-002
title: Contract Tests
family: behavioral
family_num: 02
oracle: high
independence: high
scope: service-boundary
latency: minutes
actionability: guiding
type: predictive
stack_level: integration-tests
categories:
  - Behavioral
  - Boundary Assumptions
  - Microservices
  - Guiding Sensors
see_also:
  - SO-001
  - SO-004
  - change-family
  - structural-family
last_reviewed: 2026-08-23
---

Does service A continue satisfying the assumptions of service B? Contract
tests are a sensor of *boundary assumptions* — the implicit agreements
between independent components about what the interface between them
promises.

## Contracts measure boundary assumptions

A *contract* is a specification of what one component promises to provide
and what another component is allowed to assume. Contract tests verify that
both sides of the boundary continue to honor these promises as the system
evolves.

```
# Consumer-driven contract
Service B (consumer) defines:
  "I expect GET /users/{id} to return
   { id: int, name: string, active: bool }"

Service A (provider) must satisfy:
  its response matches this shape
  the field types are correct
  the endpoint exists and responds
```

The sensor detects *breaking changes* — when a provider modifies its API in
a way that violates the assumptions its consumers depend on. This is
particularly powerful in microservice architectures where independent teams
deploy independently.

> Contracts measure boundary assumptions. Types measure a particular class
> of structural inconsistency. Contract tests are the boundary-level version
> of what type checkers are at the module level: both enforce structural
> promises, but at different scopes and different feedback latencies.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — a contract violation is a definite bug |
| Independence | High when consumer-driven — consumer defines the contract |
| Scope | Service-boundary-level |
| Feedback latency | Minutes |
| Actionability | Guiding — shows exactly which contract clause was violated |
| Type | Predictive — catches breaking changes before deployment |

## What it cannot detect

Contract tests verify the *shape* of communication, not its *meaning*. A
response that has the right fields and types but contains wrong values will
pass a contract test. They also cannot detect
[integration failures](catalog.html#behavioral) that emerge from the
*interaction* of correct components producing incorrect emergent behavior.
