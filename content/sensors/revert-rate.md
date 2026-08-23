---
id: SO-009
title: Revert Rate
family: evolution
family_num: "09"
oracle: medium
independence: high
scope: module
latency: days
actionability: exploratory
type: retrospective
stack_level: user-outcome
categories:
  - Evolution
  - Black-Box Sensors
  - Maintainability
see_also:
  - SO-009b
  - SO-009c
  - SO-009d
last_reviewed: 2026-08-23
---

How often does this area get reverted? A *black-box sensor* of
maintainability — you don't need to understand `FooManagerFactoryImpl`, you
can observe: 27 changes in six months, 8 reverts, 4 incidents, touched by
11 teams. That's a signal.

Revert rate is a retrospective sensor: it tells you that changes in this
area have historically been unreliable, without reading a single line of
code. High revert rate is a leading indicator of complexity, poor testing,
or misunderstood requirements.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — reversion correlates with problems |
| Independence | High — computed from git history |
| Scope | Module-level |
| Feedback latency | Days to weeks |
| Actionability | Exploratory — shows the pattern, you investigate |
| Type | Retrospective |

## What it cannot detect

Revert rate can't tell you *why* changes are reverted. It identifies
where attention is needed, not what the fix is. Also misses problems that
were fixed forward rather than reverted.

## Tooling

- git log
- git-quick-stats
- CodeScene

## References

- https://github.com/erikbern/git-quick-stats
