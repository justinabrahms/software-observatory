---
id: SO-008
title: Dependency Graph
family: architecture
family_num: 08
oracle: low
oracle_note: coupling is a risk factor, not a bug
independence: high
independence_note: graph is computed from the code
scope: system
latency: seconds
actionability: exploratory
actionability_note: shows the graph, you interpret it
type: predictive
stack_level: static-analysis
categories:
- Architecture
see_also:
- SO-008b
- SO-008c
- SO-008d
last_reviewed: '2026-08-24'
references:
- title: A Novel Approach for Estimating Truck Factors
  year: 2016
  tier: II
  url: https://arxiv.org/pdf/1604.06766
  kind: paper
  authors: Guilherme Avelino, Leonardo Passos, Andre Hora, Marco Tulio Valente
  venue: arXiv 1604.06766 (companion to ICPC 2016)
- title: Do Developers Update Their Library Dependencies?
  year: 2017
  tier: II
  url: https://arxiv.org/abs/1709.04621
  kind: paper
  authors: Raula Gaikovina Kula, Daniel M. German, Ali Ouni, Takashi Ishio, Katsuro Inoue
  venue: Empirical Software Engineering
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

## In practice

The reading is a list of edges plus a few numbers, often surfaced by
an import-boundary tool refusing an edge:

```
import-linter: forbidden import detected
  src/api/views.py -> src/db/session
  contract "api must not import db internals": BROKEN (1 violation)

dependency-cruiser: circular
  src/auth/token.ts -> src/auth/session.ts -> src/auth/token.ts
```

| Metric | Reading | Read as |
|--------|---------|---------|
| Fan-in | 47 modules import `util.ts` | Blast radius of any change to it |
| Fan-out | `checkout.ts` imports 31 modules | Fragility: any of them can break it |
| Cycles | auth <-> session | Coupling that blocks separate testing |
| Instability | 9 changes to `core.py` this quarter | Every dependent pays churn tax |

The numbers are not verdicts; they are the inputs to a judgment about
where change will be expensive. Read the graph against recent change
history, because a stable hub is cheap and a churning hub is a
bottleneck, and the graph alone cannot tell them apart. Treat a
single module with high fan-in and high instability as the highest-
priority refactoring target in the codebase.

## Response playbook

When the graph reads badly:

1. **Find the one edge that matters most.** The highest-risk edge is
   the one into the most-changed module with the widest fan-in, not
   the one that looks worst in the diagram.
2. **Break cycles at the import level first.** Move the shared type
   or interface into a leaf module so both sides depend on it and
   not on each other.
3. **Introduce a boundary rule while the graph still obeys it,**
   then make it blocking: the boundary can only be enforced from a
   position of compliance.
4. **Track the metric, not the diagram.** Fan-in of hot modules and
   cycle count are cheap to trend; re-rendering the whole graph is
   theater.

## How it gets gamed

- **Boundary exceptions.** An import-linter exemption list that
  grows faster than the violations it was created to clear, until
  the rule is a museum of grandfathered breaks.
- **Lazy-import laundering.** Importing the forbidden module inside
  a function body so the static graph never sees the edge. The
  coupling remains; only its visibility is removed.
- **Diagram theater.** Producing a beautiful architecture diagram
  from the graph on the day of review and never diffing it against
  the code again.

The meta-signal is exemptions per quarter: if the exception list
grows while the rule count is flat, the sensor is being spent.

## What it cannot detect

The dependency graph shows structural coupling, not *behavioral* coupling —
modules that change together for reasons the graph can't see. That requires
[change coupling](catalog.html#evolution) analysis.
