---
id: SO-001d
title: Schema Validator
family: structural
family_num: "01"
oracle: high
independence: high
scope: service
latency: seconds
actionability: guiding
type: predictive
stack_level: static-analysis
categories:
  - Structural
  - Boundary Assumptions
  - Guiding Sensors
see_also:
  - SO-001
  - SO-001c
  - SO-002
last_reviewed: 2026-08-23
---

Structural coherence at the boundary of the system. OpenAPI/GraphQL schema
validation, Terraform plan, Kubernetes admission validation, SQL parser/type
checker — all of these answer: *is this a valid instance of the expected
shape?*

Where a [type checker](type-checker.html) validates internal coherence,
schema validators validate boundary coherence: does this API request match
the contract? Does this infrastructure definition resolve?

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — schema violations are definitive |
| Independence | High — schema is external to the implementation |
| Scope | Service-level |
| Feedback latency | Seconds |
| Actionability | Guiding — shows which field violates which constraint |
| Type | Predictive |

## What it cannot detect

Schema validation cannot detect whether a valid request produces the
correct [behavioral result](catalog.html#behavioral). It checks shape, not
meaning.

## Tooling

- OpenAPI Validator
- Terraform plan
- kubectl admission
- sqlfluff

## References

- Detecting Data Errors: Where are we and what needs to be done? (2016, tier I) — https://www.vldb.org/pvldb/vol9/p993-abedjan.pdf
- Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift (2019, tier I) — https://arxiv.org/pdf/1810.11953

- OpenAPI Specification: https://spec.openapis.org
- Kubernetes Admission Controllers: https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/