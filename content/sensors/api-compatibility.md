---
id: SO-007c
title: API Compatibility
family: change
family_num: '07'
oracle: high
oracle_note: breaking changes are definitive
independence: high
independence_note: schema/contract is external
scope: service
latency: seconds
actionability: guiding
actionability_note: shows which API surface changed
type: predictive
stack_level: integration-tests
categories:
- Change
- Boundary Assumptions
see_also:
- SO-002
- SO-007
- SO-007d
last_reviewed: '2026-08-24'
references:
- title: 'I Depended on You and You Broke Me: An Empirical Study of Manifesting Breaking Changes in Client Packages'
  year: 2023
  tier: II
  url: https://arxiv.org/abs/2301.04563
  kind: paper
  authors: Suhaib Mujahid, Diego Elias Costa, Rabe Abdalkareem, Emad Shihab and others
  venue: ACM TOSEM
- title: Breaking Bad? Semantic Versioning and Impact of Breaking Changes in Maven Central
  year: 2022
  tier: II
  url: https://arxiv.org/abs/2110.07889
  kind: paper
  authors: Lina Ochoa, Thomas Degueule, Jean-Rémy Falleri, Jurgen Vinju
  venue: Empirical Software Engineering 27
- title: revapi
  url: https://revapi.org
  kind: tool
  description: API compatibility checking for JVM
- title: Akka
  kind: tool
  url: https://akka.io
  description: Actor framework for JVM concurrency
- title: grpcurl
  kind: tool
  url: https://github.com/fullstorydev/grpcurl
  description: gRPC command-line client
- title: openapi-diff
  kind: tool
  url: https://github.com/OpenAPITools/openapi-diff
  description: OpenAPI spec diff tool
---

Did externally observable contracts change? A sensor of *boundary stability*
— can old and new versions coexist?

API compatibility checking verifies that a change doesn't break existing
consumers. This is the [contract test](contract-tests.html) applied to
change: not "does the contract hold now" but "did the contract change
between versions."

## In practice

The reading is a classified diff of the API surface:

```
openapi-diff old.yaml new.yaml
BREAKING: removed endpoint GET /v1/invoices/{id}/export
BREAKING: changed type of Invoice.total: number -> string
NON-BREAKING: added optional query param `cursor` to GET /v1/invoices
NON-BREAKING: added endpoint POST /v1/invoices/{id}/void
```

The classification is the sensor's opinion; the consumer list is the
verdict. A "breaking" change with zero consumers is safe, and a
"non-breaking" change, like flipping a default, can break every
consumer that relied on the old behavior.

So the reading has two halves and neither can be skipped. The diff
half says what changed in the contract; the consumer half says who
depends on the old shape. For libraries, the consumer list is the
package index; for services, it is telemetry of which fields and
endpoints traffic actually touches. A compatibility check run without
the consumer half is a style review of the diff, not a prediction of
breakage.

## Response playbook

When the check reports a breaking change:

1. **Confirm the consumers before anything else.** An endpoint with
   zero traffic and zero imports is cheap to remove; the diff
   cannot tell you whether this is that endpoint.
2. **If consumers exist, make it additive.** Ship the new surface
   alongside the old, migrate callers, and remove the old surface
   only after the telemetry confirms nobody is left.
3. **If removal is forced, version it.** A major-version bump or a
   `/v2` prefix is the honest signal to consumers; a silent removal
   is not.
4. **Automate the check as a merge gate.** Compatibility review by
   human eyeball misses default-value and ordering changes that the
   diff tool would catch.

## How it gets gamed

- **Deprecation without removal.** Marking a surface deprecated and
  never deleting it, so the consumer list grows stale and the
  compatibility surface calcifies into something nobody can change.
- **Semantic breaks that pass the diff.** Changing the meaning of a
  field or an error code while keeping the types identical. The
  check passes; consumers break. [Contract
  tests](contract-tests.html) are the sensor for that half.
- **Version-bump laundering.** Reclassifying a breaking change as a
  "platform migration" so the compatibility gate does not run on
  it.

The meta-signal is consumer telemetry coverage: the fraction of the
API surface with real usage data behind its compatibility verdicts.

## What it cannot detect

API compatibility checks the *shape* of the interface, not the
*behavioral meaning*. A response with the same fields and types but
different semantics will pass compatibility checks.
