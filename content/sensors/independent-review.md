---
id: SO-010
title: Independent Review
family: comprehension
family_num: "10"
oracle: medium
independence: medium
scope: module
latency: hours
actionability: guiding
type: predictive
stack_level: static-analysis
categories:
  - Comprehension
  - Epistemic Accessibility
see_also:
  - SO-010b
  - SO-010c
  - SO-010d
last_reviewed: 2026-08-23
---

Can another engineer explain what this does? A sensor of *epistemic
accessibility* — if humans can't understand the system, that's itself a
correctness risk.

Independent review is the oldest comprehension sensor: someone who didn't
write the code reads it and attempts to explain its behavior. Disagreement
between author and reviewer reveals implicit assumptions, missing context,
and unclear logic.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — subjective, but disagreement is signal |
| Independence | Medium — reviewer is independent of author |
| Scope | Module-level |
| Feedback latency | Hours |
| Actionability | Guiding — reviewer asks "what does this do?" |
| Type | Predictive |

## What it cannot detect

Review quality varies enormously with reviewer expertise, attention, and
time. A rubber-stamp review provides no signal. Also, review can't catch
problems in code the reviewer doesn't read carefully.

## Tooling

- GitHub PR review
- Gerrit
- Reviewable

## References

- An Empirical Study on the Effectiveness of Security Code Review (2013, tier I) — https://people.eecs.berkeley.edu/~daw/papers/coderev-essos13.pdf
- The Cost of Interrupted Work: More Speed and Stress (2008, tier I) — https://ics.uci.edu/~gmark/chi08-mark.pdf

- Fagan, 'Design and Code Inspections to Reduce Errors' (1976)