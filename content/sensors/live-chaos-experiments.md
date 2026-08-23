---
id: SO-014b
title: Live Chaos Experiments
family: adversarial
family_num: '05'
oracle: high
oracle_note: 'the system either survived the real failure or it did not'
independence: maximum
independence_note: 'the attack comes from outside the system under test'
scope: system
latency: hours
latency_note: 'scheduled experiments, observation windows'
actionability: guiding
actionability_note: 'tells you which failure mode is unhandled'
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
references:
- title: Automating Chaos Experiments in Production
  year: 2019
  tier: IV
  url: https://arxiv.org/abs/1905.04648
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
---

Fault injection against the running production system: kill a node, sever a
region, corrupt a fraction of messages, and watch whether
[runtime invariants](runtime-invariants.html) hold. The adversary here is
not hypothetical, and the environment is not a staging cluster wearing a
costume.

Live chaos is the *deployment pattern* — running [fault
injection](fault-injection.html) (the technique) against production with
real traffic. The two are distinct sensors: fault injection tests
resilience hypothetically in staging; live chaos tests it against the real
system, where unknown failure modes are the ones that actually hurt.

## In practice

A live chaos reading is the experiment report: what was injected, who was
in the blast radius, and how the invariants held up. From a regional
failover drill:

```text
experiment: sever us-east-1 to cache cluster, 15:00 UTC
blast radius: 5% of checkout traffic, feature-flag gated
abort conditions: error rate > 2%, p99 > 800 ms

  metric              baseline    during     recovery
  checkout errors     0.1%        0.9%       0.2% (after 4m)
  p99 latency         310 ms      720 ms     330 ms
  abandoned carts     12          41         15

verdict: SURVIVED WITH DEGRADATION
finding: cache stampede on failover; no request coalescing
```

Reading it well:

1. **Read the blast radius first.** It defines what the experiment was
   allowed to cost; a "pass" that needed a narrow radius may still be a
   warning.
2. **Recovery time is part of the verdict.** A system that survives but
   takes eleven minutes to settle failed the drill in every way that
   matters at 3 a.m.
3. **Compare against the abort conditions.** Note how close the run came
   to tripping them; near-misses are findings too.
4. **One run is one data point.** Production state changes weekly.
   Re-running the same experiment is how you learn whether the fix held.

## Response playbook

When a live experiment reveals a weakness:

1. **Freeze the experiment class.** If the finding implies a wider blast
   radius than planned, stop running variants of that fault until it is
   fixed.
2. **Write up the finding within 24 hours.** Fault injected, invariant
   breached, observed behavior, recovery time. Fresh detail decays fast.
3. **Quantify the production exposure.** The report says the weakness
   exists; [feature-flag exposure](feature-flag-exposure.html) and
   traffic data say how many users are standing on it today.
4. **Fix the smallest real cause.** Usually a missing timeout, a retry
   without backoff, or a failover path nobody had exercised. Ship the
   fix behind a flag if it is risky.
5. **Re-run the identical experiment.** Same fault, same radius, same
   invariants. The re-run is the proof; the fix alone is a claim.

## What it cannot detect

Failures you did not think to inject, and failures whose blast radius
exceeds the experiment's safety limits. The most dangerous production
conditions are precisely the ones a responsible chaos program refuses to
create — those remain observable only through
[incident correlation](incident-correlation.html) after nature provides them.
