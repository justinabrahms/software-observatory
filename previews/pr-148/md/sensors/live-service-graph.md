---
id: SO-015c
title: Live Service Graph Discovery
family: architecture
family_num: 08
oracle: high
oracle_note: observed traffic is not arguable
independence: high
independence_note: collected outside the services themselves
scope: system
latency: minutes
actionability: guiding
actionability_note: shows exactly which edge appeared that shouldn't exist
type: retrospective
stack_level: production-behavior
categories:
- Architecture
- Production Sensors
see_also:
- SO-008b
- SO-006c
- SO-006
- SO-008
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

## In practice

A typical reading is the discovered edge list diffed against the declared
architecture:

| Edge | Declared | Observed (7d) | Verdict |
|------|----------|---------------|---------|
| checkout -> billing | yes | 1.2M req/day | expected |
| checkout -> legacy-auth | no | 8,412 req/day | violation |
| search -> checkout | no | 0 | ok |

Reading it well:

- **The graph alone is not a sensor.** Observed edges become evidence
  only when compared against the declared architecture. Without intent,
  you have a picture, not a finding.
- **New edges are the signal.** Long-standing violations are known debt;
  an edge that appeared since the last reading is what deserves a page.
- **Volume separates signal from noise.** Eight thousand calls a day is a
  code path someone shipped. Twelve calls is a health check or a
  misconfiguration. Both deserve a look, but not the same look.
- **Mind the window.** A month-end batch job is invisible to a 7-day
  window that ends mid-month. Read the graph over windows long enough to
  contain the rarest real traffic.

## Response playbook

When the discovered graph shows an edge the declared architecture does
not allow:

1. **Confirm the edge is real and current.** Check the observation window
   and the call volume. Twelve calls in seven days from a health check
   and 1.2 million calls a day from a shipping feature are both edges,
   but they are different conversations.
2. **Find the code path that makes the call.** The graph names the edge;
   the caller's codebase names the line. Search the calling service for
   the target's hostname or client configuration, and find when it was
   added.
3. **Decide intent before acting.** Either the architecture is wrong and
   the edge should be declared, or the edge is a violation that needs to
   go. The conversation between the two services' owners produces that
   decision; the graph only forces it to happen.
4. **Enforce at the boundary if the edge must die.** Removing a call
   once does not stop it coming back. If the edge is genuinely forbidden,
   put a [boundary sensor](boundary-sensors.html) on it so the next
   attempt fails at build time instead of reappearing in the graph.
5. **Keep the graph as a standing diff.** The point is not one violation
   but the trend: re-run the comparison regularly and alert on new edges,
   so violations surface in days rather than years.

## What it cannot detect

Edges that are legitimate but unwise, and edges that exist only under rare
load patterns not yet observed. The discovered graph is a lower bound on the
real one; [boundary sensors](boundary-sensors.html) enforce the upper bound
at build time, and the two are strongest together.
