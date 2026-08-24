---
id: SO-014c
title: Build Provenance & SBOM
family: structural
family_num: '01'
oracle: high
oracle_note: hash equality is unambiguous
independence: medium
independence_note: the builder attests its own output; a compromised builder signs faithfully
scope: system
scope_note: the whole artifact
latency: minutes
actionability: blocking
actionability_note: an unattested artifact does not ship
type: retrospective
stack_level: canary-shadow
categories:
- Structural
see_also:
- SO-001
- SO-014
- SO-012b
last_reviewed: '2026-08-24'
references:
- title: 'Reproducible Builds: Increasing the Integrity of Software Supply Chains'
  year: 2021
  tier: II
  url: https://arxiv.org/abs/2104.06020
  kind: paper
  authors: Chris Lamb, Stefano Zacchiroli
  venue: arXiv preprint; later IEEE Software 39 (2022) 62-70
- title: License Incompatibilities in Software Ecosystems
  year: 2022
  tier: II
  url: https://arxiv.org/abs/2203.01634
  kind: paper
  authors: Rolf-Helge Pfeiffer
  venue: arXiv 2203.01634
- title: SLSA
  url: https://slsa.dev
  kind: tool
  description: Supply chain security framework and attestation
- title: Sigstore
  url: https://sigstore.dev
  kind: tool
  description: Software supply chain signing
- title: cosign
  kind: tool
  url: https://github.com/sigstore/cosign
  description: Container signing tool
- title: in-toto
  kind: tool
  url: https://in-toto.io
  description: Software supply chain integrity framework
---

Is the artifact you are about to deploy structurally the one your pipeline
built? A software bill of materials plus build provenance attestation
(SLSA-style) answers: these sources, these dependencies, this builder, this
hash. A structural sensor aimed at the moment of deployment, where the
artifact leaves the world you control.

## In practice

A reading is two artifacts: the SBOM, and the attestation tying it to
the artifact you are about to deploy.

```
artifact:   payments-api@sha256:9f1c2b...
builder:    https://ci.internal/builders/release (SLSA level 3)
build:      run 8841, commit a41d2e9, 2026-08-19T14:02Z
signature:  verified, sigstore keyless

components:
  log4j-core        2.14.1  pkg:maven/org.apache.logging.log4j/log4j-core@2.14.1
  jackson-databind  2.15.2  pkg:maven/com.fasterxml.jackson.core/jackson-databind@2.15.2
```

Cross-referenced against the vulnerability feed, the same reading says:

| Component | Version | Finding | Severity | Verdict |
|-----------|---------|---------|----------|---------|
| log4j-core | 2.14.1 | CVE-2021-44228, remote code execution | critical | block deploy |
| jackson-databind | 2.15.2 | no known CVEs | none | clear |

Reading it well:

- **Verify the signature before reading the contents.** An SBOM you
  cannot tie to the builder is a claim, not an attestation. The hash
  comparison is the whole sensor; everything else is commentary.
- **Read versions, not names.** Two minor versions can be the
  difference between clear and critical, and name-only matching misses
  it.
- **Treat "not in the SBOM" as a finding.** A component present in the
  artifact but absent from the manifest means the SBOM was generated
  from the wrong place, usually the source tree instead of the build.

## Response playbook

When the sensor fires:

1. **Block the deploy on any mismatch.** Unverified signature, hash
   mismatch, or missing attestation all mean the artifact does not
   ship. Do not deploy first and reconcile later; the artifact leaves
   the world you control at deploy time.
2. **Block on critical vulnerability findings.** A critical CVE in a
   shipped component is a stop-ship condition. Confirm whether the
   component is reachable in your build; if it is dead weight,
   upgrade it anyway, because the next reader of the SBOM will not
   know.
3. **Rebuild from the attested source, not from the cached artifact.**
   A mismatch usually means the build ran somewhere else, or the
   cache is stale. Re-run the pipeline and compare hashes again.
4. **Escalate signature failures, not just dependency failures.** A
   vulnerable dependency is a fix; a bad or missing signature is a
   possible supply-chain event. Notify security before retrying.
5. **Record the attestation hash at deploy time.** When a CVE ships
   next quarter, you need to answer which deployments carry it, from
   the SBOM, not from memory.

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
