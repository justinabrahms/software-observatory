---
id: SO-009b
title: Change Coupling
family: evolution
family_num: 09
oracle: medium
independence: high
scope: system
latency: days
actionability: exploratory
type: retrospective
stack_level: static-analysis
categories:
- Evolution
- Hidden Coupling
- Black-Box Sensors
see_also:
- SO-009
- SO-009c
- SO-009d
- SO-008
last_reviewed: 2026-08-23
references:
- title: Organizational Volatility and its Effects on Software Defects
  year: 2010
  tier: II
  url: https://mockus.org/papers/orgQuality-slides.pdf
  kind: paper
- title: 2017 State of DevOps Report
  year: 2017
  tier: II
  url: https://dora.dev/research/2017/2017-state-of-devops-report.pdf
  kind: paper
- authors: Adam Tornhill
  title: Your Code as a Crime Scene
  year: 2015
  kind: paper
- title: CodeScene
  kind: tool
  url: ''
  description: Code analysis predicting technical debt from behavioral code
- title: git-quick-stats
  kind: tool
  url: ''
  description: Git history analysis script
---

Which files repeatedly change together? A sensor of *hidden coupling* — the
repository itself becomes a sensor, no code reading required.

Change coupling reveals relationships the [dependency
graph](dependency-graph.html) can't see: modules that have no structural
dependency but always change together. This is often a sign of shared
business rules, duplicated logic, or implicit coordination.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — coupling correlates with risk |
| Independence | High — computed from git history |
| Scope | System-level |
| Feedback latency | Days |
| Actionability | Exploratory — shows the coupling clusters |
| Type | Retrospective |

## What it cannot detect

Change coupling shows correlation, not causation. Files that change together
may do so for coincidental reasons (same sprint, same author) rather than
structural coupling.
