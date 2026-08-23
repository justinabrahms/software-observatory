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
last_reviewed: 2026-08-23
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

Supply chain security is a deeper topic than this catalog covers.
Build provenance and SBOMs are one sensor in the structural family — they
verify the artifact matches what the pipeline built — but the broader
practice of supply chain security (dependency vulnerabilities, artifact
signing trust roots, runtime attestation, policy enforcement) deserves its
own resources. See [SLSA](https://slsa.dev) and
[Sigstore](https://sigstore.dev) for dedicated treatment.

## Tooling

- SLSA
- cosign
- Sigstore
- in-toto

## References

- Reproducible Builds: Increasing the Integrity of Software Supply Chains (2021, tier II) — https://arxiv.org/abs/2104.06020
- License Incompatibilities in Software Ecosystems (2022, tier II) — https://arxiv.org/abs/2203.01634

- SLSA: https://slsa.dev
- Sigstore: https://sigstore.dev