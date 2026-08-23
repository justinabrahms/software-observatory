---
id: SO-013b
title: Pre-Promotion Invariant Gates
family: invariants
family_num: '04'
oracle: high
independence: high
scope: system
latency: minutes
actionability: blocking
type: predictive
stack_level: canary-shadow
categories:
- Invariants
- Deployment Safety
see_also:
- SO-004
- SO-007
- SO-012b
last_reviewed: 2026-08-23
references:
- title: OPA Gatekeeper
  url: https://open-policy-agent.github.io/gatekeeper/
  kind: tool
  description: Kubernetes policy enforcement via Open Policy Agent
- title: Kyverno
  kind: tool
  url: https://kyverno.io
  description: Kubernetes-native policy management
- title: Conftest
  kind: tool
  url: https://www.conftest.dev
  description: Policy testing for structured data
- title: HashiCorp Sentinel
  kind: tool
  url: https://developer.hashicorp.com/sentinel
  description: Policy-as-code for Terraform
---

Invariants checked at the moment of promotion, before a change can reach
users: migrations must be backward-compatible, no PII column may be added
without an encryption flag, the new schema must accept every message the old
one could. Where [canary analysis](canary-analysis.html) watches behavior
diverge on real traffic, these gates refuse the rollout outright when a
declared rule is violated.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — the rule either holds for this change or it does not |
| Independence | High — enforced by the pipeline, not the team shipping the change |
| Scope | System |
| Feedback latency | Minutes |
| Actionability | Blocking |
| Type | Predictive |

## What it cannot detect

Violations of rules nobody declared, and rules whose declaration is wrong.
The gate is only as good as the invariant list, which is why the list itself
deserves [independent review](independent-review.html).
