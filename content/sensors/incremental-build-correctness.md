---
id: SO-014d
title: Incremental Build Correctness
family: change
family_num: '07'
oracle: medium
independence: high
scope: codebase
latency: minutes
actionability: guiding
type: retrospective
stack_level: static-analysis
categories:
- Change
- Build Systems
see_also:
- SO-007b
- SO-014c
- SO-001
last_reviewed: 2026-08-23
references:
- title: 'Reproducible Builds: Increasing the Integrity of Software Supply Chains'
  year: 2021
  tier: II
  url: https://arxiv.org/abs/2104.06020
  kind: paper
- title: An Empirical Analysis of Build Failures in the Continuous Integration Workflows
    of Java-Based Open-Source Software
  year: 2017
  tier: II
  url: https://dsg.tuwien.ac.at/team/trausch/pub/PID4727015.pdf
  kind: paper
- title: Bazel
  url: https://bazel.build
  kind: tool
  description: Google's build system
- title: Buck
  kind: tool
  url: https://buck.build
  description: Meta's build system
- title: Nix
  kind: tool
  url: https://nixos.org
  description: Reproducible build system and package manager
- title: ccache
  kind: tool
  url: https://ccache.dev
  description: Compiler cache for fast rebuilds
---

Did the build system actually rebuild everything this change touched?
Incremental builds and remote caches save hours, and silently shipping a
stale artifact is the price when the dependency graph they trust is wrong.
This sensor compares what the change *should* have invalidated against what
the build *did* invalidate.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — divergence between declared and actual rebuild sets is meaningful but noisy |
| Independence | High — measures the build system, which the change author does not control |
| Scope | Codebase |
| Feedback latency | Minutes |
| Actionability | Guiding — points at the under-declared dependency edge |
| Type | Retrospective |

## What it cannot detect

Changes whose *semantic* effect exceeds their declared dependencies in ways
no graph captures (a shared constant edited in a header the graph treats as
irrelevant). That class of surprise is what
[API compatibility](api-compatibility.html) and
[integration tests](integration-tests.html) exist for.
