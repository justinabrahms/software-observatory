---
id: SO-014b
title: Live Chaos Experiments
family: adversarial
family_num: "05"
oracle: high
independence: maximum
scope: system
latency: hours
actionability: guiding
type: retrospective
stack_level: production-behavior
categories:
  - Adversarial
  - Resilience
see_also:
  - SO-005c
  - SO-006c
  - SO-004b
last_reviewed: 2026-08-23
---

Fault injection against the running production system: kill a node, sever a
region, corrupt a fraction of messages, and watch whether
[runtime invariants](runtime-invariants.html) hold. The adversary here is
not hypothetical, and the environment is not a staging cluster wearing a
costume.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — the system either survived the real failure or it did not |
| Independence | Maximum — the attack comes from outside the system under test |
| Scope | System |
| Feedback latency | Hours (scheduled experiments, observation windows) |
| Actionability | Guiding — tells you which failure mode is unhandled |
| Type | Retrospective |

## What it cannot detect

Failures you did not think to inject, and failures whose blast radius
exceeds the experiment's safety limits. The most dangerous production
conditions are precisely the ones a responsible chaos program refuses to
create — those remain observable only through
[incident correlation](incident-correlation.html) after nature provides them.

## Tooling

- Chaos Mesh
- Gremlin
- Litmus

## References

- Chaos Engineering: https://principlesofchaos.org
