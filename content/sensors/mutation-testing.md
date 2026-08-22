---
id: SO-003
title: Mutation Testing
family: test-effectiveness
family_num: 03
oracle: high
independence: medium
scope: function
latency: minutes-hours
actionability: guiding
type: adversarial
stack_level: mutation-testing
categories:
  - Test Effectiveness
  - Adversarial
  - Test Sensitivity
  - Guiding Sensors
see_also:
  - SO-003b
  - behavioral-family
  - SO-005
  - SO-005b
---

Take `if user.is_admin: allow()` and mutate it to
`if not user.is_admin: allow()`. If all your tests still pass, your tests did
not actually establish the behavior you thought they established. Mutation
testing is a sensor of test *sensitivity* rather than test *presence* — and
it may be one of the most interesting sensors in the entire catalog.

## The hierarchy of test evidence

Mutation testing reveals a useful hierarchy of evidence about tests:

```
coverage      → execution (did we run this line?)
mutation      → detection (would we catch a wrong impl?)
property      → behavioral invariants (always true?)
telemetry     → actual-world behavior (what happened?)
```

A project can have 90% line coverage while mutation testing finds large
numbers of mutations that tests don't detect. Coverage measures execution.
Mutation measures whether the test would notice if the implementation were
wrong. That is a massive distinction.

## What it looks like

```
# Original code
if user.is_admin:
    allow()

# Mutations injected
if not user.is_admin: allow()    # negated condition
if True: allow()                 # removed condition
if False: allow()                # forced false
if user.is_admin: deny()         # flipped outcome

# If all tests pass with these mutations...
# ...the tests are not establishing the behavior they claim
```

> Mutation testing is the first sensor that asks not "did the code execute?"
> but "would we have noticed if it were wrong?" That shift — from execution
> to detection — is the foundation of test effectiveness as a distinct
> category from test presence.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — a surviving mutation is strong evidence of a test gap |
| Independence | Medium — the test author writes the tests being evaluated |
| Scope | Function-level |
| Feedback latency | Minutes to hours |
| Actionability | Guiding — shows the exact untested mutation |
| Type | Adversarial — it actively tries to make tests fail |

## What it cannot detect

Mutation testing cannot detect *missing behavior* — if the code never
implements a feature, there's nothing to mutate. It also cannot detect
[integration failures](catalog.html#behavioral) that emerge only when
components are connected. And it is computationally expensive: each mutation
is a full test run.
