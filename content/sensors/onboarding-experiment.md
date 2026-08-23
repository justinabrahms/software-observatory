---
id: SO-010c
title: Onboarding Experiment
family: comprehension
family_num: "10"
oracle: low
independence: high
scope: module
latency: weeks
actionability: exploratory
type: retrospective
stack_level: static-analysis
categories:
  - Comprehension
  - Knowledge Concentration
see_also:
  - SO-010
  - SO-010b
  - SO-010d
last_reviewed: 2026-08-23
---

How long does it take a competent engineer to safely modify this subsystem?
A sensor of *knowledge concentration* measured in onboarding time.

The onboarding experiment is the most direct sensor of epistemic
accessibility: give a competent engineer a task in an unfamiliar area and
measure how long it takes them to complete it safely. Long onboarding times
indicate implicit knowledge, missing documentation, or excessive coupling.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Low — onboarding time correlates with complexity |
| Independence | High — measured from external engineers |
| Scope | Module-level |
| Feedback latency | Weeks |
| Actionability | Exploratory — shows where onboarding is slow |
| Type | Retrospective |

## What it cannot detect

Onboarding time conflates code complexity with many other factors: tooling,
build process, test infrastructure, team availability. A slow onboarding may
not reflect code quality at all. The methodology also matters:

- **Who** do you onboard? A junior measures documentation quality; a senior
  measures code legibility. The choice changes the signal.
- **Prior system knowledge** — an engineer who's seen a similar system
  elsewhere will onboard faster regardless of this system's clarity.
- **Noise** — a single onboarding is anecdote. You need repeated measures
  to get a signal, and repeated onboarding is expensive.

Treat the onboarding experiment as a structured protocol (same task, same
seniority level, same prior-knowledge screening), not a one-off timer.
