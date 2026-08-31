---
id: SO-008b
title: Architecture Fitness Functions
family: architecture
family_num: 08
oracle: high
oracle_note: a violation is definitive
independence: high
independence_note: rules are external to the code
scope: system
latency: seconds
actionability: guiding
actionability_note: shows which rule was violated and where
type: predictive
stack_level: static-analysis
categories:
- Architecture
- Boundary Sensors
see_also:
- SO-008
- SO-008c
- SO-008d
references:
- title: ArchUnit
  url: https://www.archunit.org
  kind: tool
  description: Architecture testing for Java
- title: NetArchTest
  kind: tool
  url: https://github.com/BenMorris/NetArchTest
  description: .NET architecture rules testing
- title: dependency-cruiser
  kind: tool
  url: https://github.com/sverweij/dependency-cruiser
  description: JavaScript/TypeScript dependency analysis
---

`frontend -> application -> domain -> infrastructure`, and fail if `domain
-> infrastructure`. A sensor of *architectural drift*.

Architecture fitness functions are executable assertions about the structure
of the code. They fail when the architecture violates a rule: a domain layer
importing infrastructure, a service bypassing its API, a forbidden
dependency forming. They turn architectural rules from prose into
computational gates.

## In practice

A fitness function reading is a test result: the rule either holds or it
does not, and the failure names the exact violating edge. In Java with
ArchUnit:

```
Architecture Violation [Priority: MEDIUM] - Rule
'no classes that reside in package '..domain..' should depend on
classes that reside in package '..infrastructure..'' was violated
(1 times):
Class <com.acme.domain.InvoiceService> depends on
<com.acme.infrastructure.EmailClient> in (InvoiceService.java:42)
```

In CI it arrives as one failing check among the rest, no different in
shape from a unit test failure. Reading it well:

1. **The violation message is the diagnosis.** Unlike most sensors, the
   output names both the rule and the exact dependency that broke it.
   There is no investigation step between reading and acting.
2. **A new violation is cheaper than an old one.** The reading that
   matters is the delta: did this change introduce the edge? Catching
   drift at merge time is the whole point of the sensor.
3. **Watch the violation count per rule over time.** A rule with a
   frozen baseline of 40 grandfathered violations that is not shrinking
   is a rule the team has stopped believing in.
4. **Treat every rule as a claim about the architecture.** If the team
   cannot say why the rule exists, the fitness function is asserting
   folklore, and its failure is noise, not signal.

## How it gets gamed

Fitness functions are tests, so they can be tuned like tests:

- **Grandfathering forever.** Freeze the current violations in a
  baseline and promise to burn it down later. If the baseline never
  shrinks, the rule applies only to code nobody has written yet, and
  the architecture it protects keeps eroding underneath.
- **Tuning the rule to pass.** When a rule fails, the fast fix is
  narrowing its scope, excluding the offending package, or rewording
  the matcher until the suite is green again. The rule now describes
  the code as it is, not as it should be.
- **Rules that assert nothing.** A fitness function that every change
  passes is a sensor with its mouth taped. Rules need to be able to
  lose: if a rule has never fired, either the architecture is perfect
  or the rule is toothless, and it is usually the second.

The meta-signal is the ratio of rule changes to code changes. When the
rules move to accommodate the code instead of the reverse, the sensor
has been inverted.

## Response playbook

When a fitness function fails or its output stops being trusted:

1. **Read the violation, not just the failure.** The output names the
   violating dependency and its location. Decide explicitly whether the
   new edge is wrong or whether the rule is wrong.
2. **Fix the edge if the rule is right.** Restructure the change so the
   forbidden dependency does not form. This is usually a small refactor
   at merge time, not a project.
3. **Amend the rule in a separate, reviewed change if the rule is
   wrong.** Rule changes deserve their own commit and a reason, so the
   tuning described above is visible rather than smuggled in.
4. **Burn down the baseline.** If violations are grandfathered, assign
   each one an owner or a deletion date. A frozen baseline is a rule in
   name only.
5. **Add the rule that just failed for the first time.** If drift was
   caught by review rather than by a fitness function, codify the
   principle as a new rule so the next drift fails in CI.

## What it cannot detect

Fitness functions only check rules you've *codified*. Implicit architectural
rules that haven't been expressed as functions are invisible to this sensor.
