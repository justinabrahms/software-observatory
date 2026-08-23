---
id: SO-013b
title: Pre-Promotion Invariant Gates
family: invariants
family_num: '04'
oracle: high
oracle_note: 'the rule either holds for this change or it does not'
independence: high
independence_note: 'enforced by the pipeline, not the team shipping the change'
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

## In practice

A pre-promotion gate reading is a policy verdict at deploy time, before
any traffic moves. With a tool like OPA or Kyverno, the promotion step
prints the violated rule and refuses to continue:

```
gate: deny migration-not-backward-compatible
change: deploy/api v2.41.0
violation: migration 20260823_add_status.sql drops column
           "orders.legacy_state"; old pods still read it.
result: PROMOTION BLOCKED
```

The verdict is binary and the output names the invariant, so the reading
is unambiguous. Habits that keep it useful:

1. **Read the rule name first, the diff second.** The gate tells you
   which declared invariant failed. The fix usually follows directly:
   make the migration additive, ship the drop in a later release.
2. **A blocked promotion is cheap; an unblocked violation is not.**
   The gate firing at promotion is the sensor doing its job. The cost
   to compare against is the same change caught by
   [canary analysis](canary-analysis.html) or by users.
3. **Watch how often the gate fires.** A rule that blocks every other
   deploy is either catching real drift or is written against how the
   team actually works. Both deserve attention; only one is fixed by
   editing the rule.
4. **Note what the gate did not check.** The absence of a rule is
   invisible in the output. The invariants list itself is the artifact
   to review.

## How it gets gamed

The gate enforces declared rules, so the gaming happens at declaration
and exception time:

- **Exception inflation.** Every rule grows an exceptions list, and the
  exceptions outlive the emergencies that justified them. A gate with a
  long standing exception file is enforcing the rules minus the parts
  the team found inconvenient.
- **Rule wording as evasion.** When a promotion blocks, the fast path
  is editing the policy until the change passes: narrowing "no dropped
  columns" to "no dropped columns except in orders." The gate still
  reads as enforced while covering less.
- **Promoting outside the gate.** A hotfix path, a manual deploy, or a
  different pipeline that skips the policy step. The gate protects the
  front door, and changes start leaving through the side.

The meta-signal is the exception count per rule and how long exceptions
live. Permanent exceptions are rule deletions wearing a badge.

## Response playbook

When a pre-promotion gate blocks a change, or its output loses trust:

1. **Read the violated invariant and fix the change, not the gate.**
   Most blocks are repairable at source: make the migration additive,
   split the schema change from the deploy, add the missing flag.
2. **If the rule is wrong, change it in a reviewed policy commit.**
   Rule edits need the same scrutiny as code, or the gate becomes
   negotiable at deploy time, which is the worst time to negotiate.
3. **Grant exceptions with an expiry.** If a real emergency requires
   bypassing the gate, record it with an owner and a date. Expired
   exceptions should fail loudly, not lapse silently.
4. **After any incident, ask which invariant was missing.** If a
   failure slipped through promotion, the gap is a rule nobody
   declared. Add it, and let the gate list grow from incidents rather
   than from guesses.

## What it cannot detect

Violations of rules nobody declared, and rules whose declaration is wrong.
The gate is only as good as the invariant list, which is why the list itself
deserves [independent review](independent-review.html).
