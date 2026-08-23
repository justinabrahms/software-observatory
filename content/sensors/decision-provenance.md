---
id: SO-010d
title: Decision Provenance
family: comprehension
family_num: '10'
oracle: low
independence: high
scope: module
latency: days
actionability: exploratory
type: retrospective
stack_level: static-analysis
categories:
- Comprehension
- Archaeological Accessibility
see_also:
- SO-010
- SO-010b
- SO-010c
last_reviewed: 2026-08-23
references:
- authors: Michael Nygard
  title: Documenting Architecture Decisions
  year: 2017
  kind: paper
- title: ADR
  url: https://adr.github.io
  kind: tool
- title: ADRs
  kind: tool
  url: ''
  description: Architecture Decision Records
- title: Conventional Commits
  kind: tool
  url: ''
  description: Structured commit message specification
- title: git blame
  kind: tool
  url: ''
  description: Git history annotation per line
---

Can you answer "why is this weird thing here?" A sensor of *archaeological
accessibility* — can you determine why code exists, not just what it does?

Decision provenance traces the history of a design decision: the ADRs, PRs,
discussions, and constraints that led to the current code. When provenance
is lost, the code becomes untouchable — nobody knows whether it can be
changed safely.

## How it's recorded

- **ADRs** (Architecture Decision Records, Michael Nygard's pattern) —
  short documents capturing context, decision, and consequences. The
  canonical technique.
- **Commit conventions** — linking commits to issues, explaining *why*
  not just *what* (Conventional Commits, referencing tickets).
- **`git blame` / `git log -S`** — the fallback when no explicit provenance
  was recorded. The archaeology tool of last resort.

Provenance decays — an ADR from three years ago may explain why the code
was *added* but not why it's *still there*. Periodic re-justification keeps
provenance alive.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Low — missing provenance is a risk factor |
| Independence | High — history is independent of current code |
| Scope | Module-level |
| Feedback latency | Days |
| Actionability | Exploratory — shows whether provenance exists |
| Type | Retrospective |

## What it cannot detect

Decision provenance can only exist where decisions were *recorded*. Decisions
made verbally, in deleted branches, or in private messages are invisible to
this sensor.
