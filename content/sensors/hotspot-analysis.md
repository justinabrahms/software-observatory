---
id: SO-008c
title: Hotspot Analysis
family: architecture
family_num: 08
oracle: low
independence: high
scope: module
latency: minutes
actionability: exploratory
type: retrospective
stack_level: static-analysis
categories:
- Architecture
- Complexity
- Risk Concentration
see_also:
- SO-008
- SO-008b
- SO-008d
- evolution-family
last_reviewed: 2026-08-23
references:
- title: A Novel Approach for Estimating Truck Factors
  year: 2016
  tier: II
  url: https://arxiv.org/pdf/1604.06766
  kind: paper
- title: Don't Touch My Code! Examining the Effects of Ownership on Software Quality
  year: 2011
  tier: II
  url: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/bird2011dtm.pdf
  kind: paper
- authors: Adam Tornhill
  title: Your Code as a Crime Scene
  year: 2015
  kind: paper
- title: CodeScene
  kind: tool
  url: https://codescene.com
  description: Code analysis predicting technical debt from behavioral code
- title: crux
  kind: tool
  url: https://github.com/mauricio/crux
  description: Code complexity analysis tool
- title: git-quick-stats
  kind: tool
  url: https://github.com/arzzen/git-quick-stats
  description: Git history analysis script
---

Change frequency times complexity. Identifies places where the system is
simultaneously *difficult* and *frequently changed* — more interesting than
"files with the most lines."

Hotspot analysis combines two signals: how complex a module is
(cyclomatic complexity, nesting depth) and how often it changes (commit
frequency). The intersection — a complex module that changes frequently — is
where risk concentrates.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Low — a hotspot is a risk indicator, not a bug |
| Independence | High — computed from git and metrics |
| Scope | Module-level |
| Feedback latency | Minutes |
| Actionability | Exploratory — shows the heat map |
| Type | Retrospective |

## What it cannot detect

Hotspot analysis doesn't tell you *why* a module changes frequently or
*whether* it's correct. It identifies where attention is needed, not what
the attention should fix.
