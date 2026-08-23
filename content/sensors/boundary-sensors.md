---
id: SO-008d
title: Boundary Sensors
family: architecture
family_num: 08
oracle: high
independence: high
scope: module
latency: seconds
actionability: guiding
type: predictive
stack_level: static-analysis
categories:
- Architecture
- Encapsulation
- Guiding Sensors
see_also:
- SO-008
- SO-008b
- SO-002
last_reviewed: 2026-08-23
references:
- title: Istio
  url: https://istio.io
  kind: tool
  description: Service mesh with traffic management and observability
- title: Linkerd
  kind: tool
  url: ''
  description: Lightweight Kubernetes service mesh
- title: Cilium
  kind: tool
  url: ''
  description: eBPF-based networking, observability, and security
- title: eBPF tools
  kind: tool
  url: ''
  description: Kernel-level observability tools
---

"This package must not import that package." A sensor of *encapsulation* and
module boundaries — computationally enforced, not prose rules.

Boundary sensors are the module-level version of [fitness
functions](fitness-functions.html): they assert that specific imports or
dependencies are forbidden. Unlike complexity metrics, they have high oracle
strength — a forbidden import is a definitive violation.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — a boundary violation is definitive |
| Independence | High — rules are external to the code |
| Scope | Module-level |
| Feedback latency | Seconds |
| Actionability | Guiding — shows exactly which import violates the boundary |
| Type | Predictive |

## What it cannot detect

Boundary sensors check structural boundaries, not [behavioral
boundaries](contract-tests.html). A module can respect import boundaries
while still violating encapsulation through shared mutable state.
