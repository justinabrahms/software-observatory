---
id: SO-008
title: Dependency Graph
family: architecture
family_num: 08
oracle: low
independence: high
scope: system
latency: seconds
actionability: exploratory
type: predictive
stack_level: static-analysis
categories:
- Architecture
- Coupling
- Dependency Analysis
see_also:
- SO-008b
- SO-008c
- SO-008d
last_reviewed: 2026-08-23
references:
- title: A Novel Approach for Estimating Truck Factors
  year: 2016
  tier: II
  url: https://arxiv.org/pdf/1604.06766
  kind: paper
- title: Do Developers Update Their Library Dependencies?
  year: 2017
  tier: II
  url: https://arxiv.org/abs/1709.04621
  kind: paper
- title: dependency-cruiser
  url: https://github.com/sverweij/dependency-cruiser
  kind: tool
  description: JavaScript/TypeScript dependency analysis
- title: import-linter
  kind: tool
  url: https://import-linter.readthedocs.io
  description: Python import linting and boundary enforcement
- title: madge
  kind: tool
  url: https://github.com/pahen/madge
  description: JavaScript dependency graph and circular dependency detection
- title: dependency-graph
  kind: tool
  url: https://github.com/jfrog/dependency-graph
  description: Gradle dependency graph plugin
---

Fan-in, fan-out, cycles, dependency depth, unstable dependencies. A sensor
of structural *coupling* between modules.

The dependency graph reveals hidden relationships: modules that import each
other transitively, cycles that create tight coupling, dependencies on
unstable (frequently changing) modules. None of these are bugs — but they're
risk factors.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Low — coupling is a risk factor, not a bug |
| Independence | High — graph is computed from the code |
| Scope | System-level |
| Feedback latency | Seconds |
| Actionability | Exploratory — shows the graph, you interpret it |
| Type | Predictive |

## What it cannot detect

The dependency graph shows structural coupling, not *behavioral* coupling —
modules that change together for reasons the graph can't see. That requires
[change coupling](catalog.html#evolution) analysis.
