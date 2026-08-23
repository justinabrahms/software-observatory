---
id: SO-005d
title: Fault Injection
family: adversarial
family_num: '05'
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
references:
- title: 'Elle: Inferring Isolation Anomalies from Experimental Observations'
  year: 2020
  tier: II
  url: https://arxiv.org/abs/2003.10554
  kind: paper
- title: 'Jepsen: MongoDB 4.2.6'
  year: 2020
  tier: II
  url: https://jepsen.io/analyses/mongodb-4.2.6
  kind: paper
- title: Chaos Engineering
  url: https://principlesofchaos.org
  kind: tool
- title: Chaos Mesh
  kind: tool
  url: https://chaos-mesh.org
  description: Kubernetes chaos engineering platform
- title: Gremlin
  kind: tool
  url: https://www.gremlin.com
  description: Managed chaos engineering service
- title: Litmus
  kind: tool
  url: https://litmuschaos.io
  description: Cloud-native chaos engineering
- title: Chaos Monkey
  kind: tool
  url: https://github.com/Netflix/chaosmonkey
  description: Netflix's instance termination service
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

Fault injection is the *technique*; [live chaos
experiments](live-chaos-experiments.html) is the *deployment pattern* of
running that technique against production. The distinction matters: fault
injection in staging tests resilience hypothetically; live chaos tests it
against the real system, with real traffic, where the failure modes you
didn't model are the ones that actually hurt you.

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
