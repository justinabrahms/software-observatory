---
id: SO-014c
title: Build Provenance & SBOM
family: structural
family_num: "01"
oracle: high
independence: high
scope: system
latency: minutes
actionability: blocking
type: retrospective
stack_level: canary-shadow
categories:
  - Structural
  - Supply Chain
see_also:
  - SO-001
  - SO-014
  - SO-012b
---

Is the artifact you are about to deploy structurally the one your pipeline
built? A software bill of materials plus build provenance attestation
(SLSA-style) answers: these sources, these dependencies, this builder, this
hash. A structural sensor aimed at the moment of deployment, where the
artifact leaves the world you control.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — hash equality is unambiguous |
| Independence | High — the attestation comes from the builder, not the deployer |
| Scope | System (the whole artifact) |
| Feedback latency | Minutes |
| Actionability | Blocking — an unattested artifact does not ship |
| Type | Retrospective |

## What it cannot detect

Malice inside the sources themselves, or a compromised builder that signs
its own output faithfully. Provenance tells you the artifact is the one the
pipeline produced; whether the pipeline was honest is a question for
[static security analysis](static-security-analysis.html) and dependency
auditing.
