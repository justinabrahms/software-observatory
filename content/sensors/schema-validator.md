---
id: SO-001d
title: Schema Validator
family: structural
family_num: '01'
oracle: high
oracle_note: schema violations are definitive
independence: high
independence_note: schema is external to the implementation
scope: service
latency: seconds
actionability: guiding
actionability_note: shows which field violates which constraint
type: predictive
stack_level: static-analysis
categories:
- Structural
- Boundary Assumptions
see_also:
- SO-001
- SO-001c
- SO-002
last_reviewed: '2026-08-24'
references:
- title: 'Detecting Data Errors: Where are we and what needs to be done?'
  year: 2016
  tier: I
  url: https://www.vldb.org/pvldb/vol9/p993-abedjan.pdf
  kind: paper
  authors: Ziawasch Abedjan, Xu Chu, Dong Deng, Raul Castro Fernandez, Ihab F. Ilyas, Mourad Ouzzani, Paolo Papotti, Michael Stonebraker, Nan Tang
  venue: PVLDB 9(12)
- title: 'Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift'
  year: 2019
  tier: I
  url: https://arxiv.org/pdf/1810.11953
  kind: paper
  authors: Stephan Rabanser, Stephan Günnemann, Zachary C. Lipton
  venue: NeurIPS 2019
- title: OpenAPI Specification
  url: https://spec.openapis.org
  kind: tool
- title: Kubernetes Admission Controllers
  url: https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/
  kind: tool
- title: OpenAPI Validator
  kind: tool
  url: https://validator.swagger.io
  description: Validate APIs against OpenAPI specs
- title: Terraform plan
  kind: tool
  url: https://developer.hashicorp.com/terraform/cli/commands/plan
  description: Infrastructure-as-code plan preview
- title: kubectl admission
  kind: tool
  url: https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/
  description: Kubernetes admission controllers
- title: sqlfluff
  kind: tool
  url: https://www.sqlfluff.com
  description: SQL linter and formatter
---

Structural coherence at the boundary of the system. OpenAPI/GraphQL schema
validation, Terraform plan, Kubernetes admission validation, SQL parser/type
checker — all of these answer: *is this a valid instance of the expected
shape?*

Where a [type checker](type-checker.html) validates internal coherence,
schema validators validate boundary coherence: does this API request match
the contract? Does this infrastructure definition resolve?

## In practice

A schema reading is a rejection at the boundary, naming the exact
field and constraint that failed:

```
Error: invalid_request
  POST /v2/invoices
  body.currency: value "usd" does not match pattern ^[A-Z]{3}$
  body.lines[2].amount: required property "amount" is missing
```

The same shape, different substrates: a Terraform plan that proposes
deleting a production resource, an admission controller refusing a
pod spec, a `kubectl apply` that fails on an unknown field. Each is
the boundary saying "this is not a valid instance."

Reading it well comes down to deciding where the truth lives. When
the request and the schema disagree, one of them is wrong, and the
validator cannot tell you which. A spike of identical rejections
usually means the schema drifted behind its producers, and loosening
the constraint without asking is how boundaries lose their meaning.
Validate on write and on read both: a shape that was valid at
ingestion can be invalid by the time anything consumes it.

## Response playbook

When validation fails:

1. **Classify before changing anything.** Is the instance wrong, or
   did the schema fall behind reality? The fix is opposite in each
   case.
2. **If the instance is wrong, fix the producer.** Hand-patching a
   payload to satisfy the validator leaves the next payload equally
   broken.
3. **If the schema is behind, version it, do not silently loosen
   it.** Widening a constraint changes the contract for every
   consumer that reads through it.
4. **For infrastructure plans, diff before apply.** A plan is a
   preview of production; read the destroy lines first.
5. **Re-run the check after every fix.** Boundary validation is
   cheap enough to run on every attempt.

## What it cannot detect

Schema validation cannot detect whether a valid request produces the
correct [behavioral result](catalog.html#behavioral). It checks shape, not
meaning.

Oracle strength varies significantly by sub-technique. A Terraform `plan`
is a near-perfect oracle of what will be applied — it shows the exact diff
the infrastructure will undergo. An OpenAPI schema is a weaker oracle of
runtime behavior — the schema can be valid while the implementation
violates it. Kubernetes admission control sits in between. The "High"
rating above reflects the strong end of this range; for schema-as-document
validation, expect closer to medium.
