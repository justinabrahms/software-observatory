---
id: SO-003b
title: Diff Coverage
family: test-effectiveness
family_num: 03
oracle: low
independence: medium
scope: diff
latency: minutes
actionability: guiding
type: predictive
stack_level: behavioral-tests
categories:
  - Test Effectiveness
  - Change
  - Coverage
  - Agentic Coding
see_also:
  - SO-003
  - change-family
  - ai-sensors
last_reviewed: 2026-08-23
---

You don't necessarily care whether some 15-year-old module has 43% coverage.
You care: *did the code I just changed have evidence attached to it?*

## The question that matters for agentic coding

Diff coverage is extremely useful for [agentic coding](catalog.html#ai-sensors).
The question isn't "is the codebase healthy?" It's:

```
"What changed, and what evidence do we have
 that the change didn't damage anything?"
```

Diff coverage answers the narrowest version: of the lines added or modified
in this diff, how many were executed by the test suite? It's a weak oracle
— execution is not correctness — but it's a sensor that the code that was
just written has *any* evidence attached to it at all.

> Diff coverage is the minimum viable sensor for change. It doesn't tell you
> the change is correct. It tells you the change was *exercised*. That's a
> necessary — though not sufficient — condition for believing the tests
> provide evidence about it.

## The hierarchy

Diff coverage sits at the intersection of test effectiveness and change
sensors:

```
line coverage      → did this line execute?
diff coverage       → did the CHANGED lines execute?
mutation testing    → would we catch a wrong impl?
```

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Low — execution ≠ correctness |
| Independence | Medium — the test author writes the tests |
| Scope | Diff-level (change-scoped) |
| Feedback latency | Minutes |
| Actionability | Guiding — shows exactly which changed lines lack coverage |
| Type | Predictive — catches untested changes before deployment |

## What it cannot detect

Diff coverage cannot tell you whether the tests that *ran* the changed code
actually *asserted* anything about its correctness. A line can execute
without any test verifying its output. It also says nothing about
[untested behavior](mutation-testing.html) that the tests don't cover.
