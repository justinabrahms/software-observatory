---
id: SO-005d
title: Fault Injection
family: adversarial
family_num: '05'
oracle: medium
oracle_note: depends on what invariants you check
independence: high
independence_note: failures are injected externally
scope: system
latency: minutes
actionability: guiding
actionability_note: shows which invariant broke under which failure
type: predictive
stack_level: canary-shadow
categories:
- Adversarial
- Resilience
see_also:
- SO-004
- SO-005
- change
last_reviewed: '2026-08-24'
references:
- title: 'Elle: Inferring Isolation Anomalies from Experimental Observations'
  year: 2020
  tier: II
  url: https://arxiv.org/abs/2003.10554
  kind: paper
  authors: Kyle Kingsbury, Peter Alvaro
  venue: arXiv 2003.10554
- title: 'Jepsen: MongoDB 4.2.6'
  year: 2020
  tier: II
  url: https://jepsen.io/analyses/mongodb-4.2.6
  kind: paper
  authors: Kyle Kingsbury (Jepsen)
  venue: jepsen.io analyses
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

## In practice

A fault-injection reading is one experiment run: the fault that was
injected, the steady-state hypothesis it was tested against, and the
verdict per invariant. From a Chaos Mesh run against staging:

```text
experiment: kill primary replica, payments-db namespace
hypothesis: p99 checkout latency stays under 400 ms; no writes are lost
duration:   10m (2m ramp, 5m fault, 3m recovery)

  invariant                      before    during    verdict
  checkout p99 < 400 ms          212 ms    385 ms    PASS
  zero lost writes               0         2         FAIL
  failover completes             n/a       41 s      PASS
```

Reading it well:

1. **The verdict is only as good as the invariants.** A run that passes
   with weak or missing checks proves nothing. Confirm the oracle was
   watching before trusting the green.
2. **Inject at realistic magnitude.** A 50 ms latency injection when the
   real dependency takes 2 s pauses tests the timeout config, not the
   failure.
3. **Every FAIL is a finding.** File it with the exact fault and the
   invariant it broke, not as tribal knowledge.
4. **One survived fault is not resilience.** Repeat across faults and
   escalate from single to compound failures.

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

## How it gets gamed

- **Shrink the blast radius to zero.** Injecting only trivial faults
  (kill one stateless replica, drop 1% of packets) keeps every run green
  while the dangerous coupling stays untested. A chaos program with a
  100% pass rate is either very resilient or very timid.
- **Aim at the redundant path.** Targeting only the components with known
  failover produces passes by construction.
- **Rerun the stale script.** The same three experiment definitions for
  years while the system changes around them; the sensor reads history,
  not the current architecture.
- **Schedule for quiet hours.** Runs only during maintenance windows
  never see the system under load, which is when real failures happen.

The meta-signal is the experiment catalog's growth: new failure modes
injected per quarter versus reruns of old ones.

## Response playbook

When an experiment breaks an invariant:

1. **File the failure as a defect.** Record the exact fault, the
   invariant that broke, and the observed deviation. "System is fragile"
   is not actionable; "replica loss loses writes for 30 s" is.
2. **Reproduce in staging before fixing.** Confirm the finding is real
   and separate resilience gaps from environment artifacts.
3. **Read the blast radius.** The secondary symptoms in the report
   usually name the actual weakness: the retry storm, the missing
   timeout, the single consumer lagging.
4. **Fix the weakest coupling first.** Usually a missing timeout, an
   unbounded retry, or a hidden hard dependency. Then re-run the same
   experiment to prove the fix.
5. **Escalate gradually.** Only widen to compound faults once single
   faults pass.

## What it cannot detect

Fault injection can only test failure modes you *thought to inject*. Unknown
failure modes (cascading failures from unexpected coupling) require
[observability](observability-events.html) to detect in production.
