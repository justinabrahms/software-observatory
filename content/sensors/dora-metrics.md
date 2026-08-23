---
id: SO-015b
title: DORA Metrics
family: evolution
family_num: 09
oracle: medium
independence: high
scope: organization
latency: days
actionability: guiding
type: retrospective
stack_level: canary-shadow
categories:
- Evolution
- Delivery Performance
see_also:
- SO-009
- SO-009b
- SO-009d
last_reviewed: 2026-08-23
references:
- title: 'Accelerate: State of DevOps 2019'
  year: 2019
  tier: II
  url: https://dora.dev/research/2019/dora-report/2019-dora-accelerate-state-of-devops-report.pdf
  kind: paper
- title: 2017 State of DevOps Report
  year: 2017
  tier: II
  url: https://dora.dev/research/2017/2017-state-of-devops-report.pdf
  kind: paper
- title: DORA
  url: https://dora.dev
  kind: tool
- authors: Forsgren et al.
  title: Accelerate
  year: 2018
  kind: paper
- title: DORA survey
  kind: tool
  url: https://dora.dev
  description: DORA research assessment survey
- title: DevOps Research Assessment
  kind: tool
  url: https://dora.dev/research/
  description: DORA's four-metric assessment tool
---

Deployment frequency, lead time for changes, change failure rate,
reliability, time to restore. Five numbers about how changes have
historically flowed through this organization — a sensor of delivery
*pattern*, answering "does our recent past look like teams that ship
safely?" Reliability was added in DORA 2023 as the fifth metric, reflecting
that stability is measured by whether the system meets its reliability
targets, not just by how fast failures are fixed.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — the metrics proxy safety; they are not safety |
| Independence | High — derived from deployment and incident records, not self-report |
| Scope | Organization |
| Feedback latency | Days |
| Actionability | Guiding — tells you which stage of the pipeline to distrust |
| Type | Retrospective |

## What it cannot detect

The cause of a bad number. DORA metrics locate the problem in time and
stage; understanding it requires [decision provenance](decision-provenance.html)
and [incident correlation](incident-correlation.html). And like all metrics
that become targets, they invite gaming — deployment frequency can be raised
by shipping trivia.
