---
id: SO-015c
title: Live Service Graph Discovery
family: architecture
family_num: 08
oracle: high
independence: high
scope: system
latency: minutes
actionability: guiding
type: retrospective
stack_level: production-behavior
categories:
- Architecture
- Production
see_also:
- SO-008b
- SO-006c
- SO-006
last_reviewed: 2026-08-23
references:
- title: Istio
  url: https://istio.io
  kind: tool
  description: Service mesh with traffic management and observability
- title: Linkerd
  kind: tool
  url: https://linkerd.io
  description: Lightweight Kubernetes service mesh
- title: Kiali
  kind: tool
  url: https://kiali.io
  description: Service mesh observability for Istio
- title: Hubble
  kind: tool
  url: https://github.com/cilium/hubble
  description: eBPF-based network observability for Kubernetes
---

The declared architecture says service A never calls service C. The live
service graph — discovered from actual traffic via a service mesh, eBPF flow
mapping, or trace aggregation — says whether that is true in production
today. A sensor of architectural *fact*, checked against architectural
*intent*.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — observed traffic is not arguable |
| Independence | High — collected outside the services themselves |
| Scope | System |
| Feedback latency | Minutes |
| Actionability | Guiding — shows exactly which edge appeared that shouldn't exist |
| Type | Retrospective |

## What it cannot detect

Edges that are legitimate but unwise, and edges that exist only under rare
load patterns not yet observed. The discovered graph is a lower bound on the
real one; [boundary sensors](boundary-sensors.html) enforce the upper bound
at build time, and the two are strongest together.
