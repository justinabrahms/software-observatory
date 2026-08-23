---
id: SO-005c
title: Differential Testing
family: adversarial
family_num: "05"
oracle: high
independence: high
scope: function
latency: minutes-hours
actionability: guiding
type: adversarial
stack_level: property-metamorphic
categories:
  - Adversarial
  - Oracle-Free
see_also:
  - SO-005
  - SO-005b
  - SO-005d
last_reviewed: 2026-08-23
---

`implementation_A(input) == implementation_B(input)`. You don't know which is
right. But disagreement is an excellent sensor.

## The oracle question

Differential testing is oracle-free: you don't need to know the correct
answer, only whether two implementations agree. This makes it powerful for
systems where computing the expected output is infeasible.

```
old implementation vs new implementation
production implementation vs reference implementation
database query vs independently computed result
two parsers
two serialization formats
compiler vs interpreter
```

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — disagreement is definitive evidence of a bug |
| Independence | High — two independent implementations |
| Scope | Function-level |
| Feedback latency | Minutes to hours |
| Actionability | Guiding — shows the divergent inputs and outputs |
| Type | Adversarial |

## What it cannot detect

If both implementations share the same bug, differential testing won't find
it. Also requires two implementations, which may not exist.
