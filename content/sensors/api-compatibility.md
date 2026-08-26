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
last_reviewed: '2026-08-26'
references:
- title: 'I Depended on You and You Broke Me: An Empirical Study of Manifesting Breaking Changes in Client Packages'
  year: 2023
  tier: II
  url: https://arxiv.org/abs/2301.04563
  kind: publication
  authors: Daniel Venturini, Filipe Roseiro Cogo, Ivanilton Polato, Marco A Gerosa, Igor
    Scaliante Wiese
  venue: ACM TOSEM
- title: Breaking Bad? Semantic Versioning and Impact of Breaking Changes in Maven Central
  year: 2022
  tier: II
  url: https://arxiv.org/abs/2110.07889
  kind: publication
  authors: Lina Ochoa, Thomas Degueule, Jean-Rémy Falleri, Jurgen Vinju
  venue: Empirical Software Engineering 27
- title: revapi
  url: https://revapi.org
  kind: tool
  description: API compatibility checking for JVM
- title: MiMa
  kind: tool
  url: https://github.com/lightbend/mima
  description: Binary compatibility checking for Scala/JVM libraries
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

API compatibility checking answers one question about a diff: did this
change break backwards compatibility? It reads the old version of the
interface and the new one, and classifies what moved between them. It
does not ask who is on the other end, and it does not need to — an
endpoint removed is a backwards-incompatible change whether anyone
called it or not.

That is the line between this sensor and [contract
tests](contract-tests.html). Contract tests ask *did we break our
consumers?* Compatibility asks *did we make a backwards-incompatible
change?* Compatibility is a property of two versions of a surface;
breakage is a property of two versions plus the people using them.

## In practice

The reading is a classified diff of the API surface:

```
openapi-diff old.yaml new.yaml
BREAKING: removed endpoint GET /v1/invoices/{id}/export
BREAKING: changed type of Invoice.total: number -> string
NON-BREAKING: added optional query param `cursor` to GET /v1/invoices
NON-BREAKING: added endpoint POST /v1/invoices/{id}/void
```

That classification is the whole reading, and its strength is that it
needs to know nothing about the outside world. `Invoice.total` moving
from number to string is incompatible whether one caller parses it or
ten thousand do. Nothing has to be deployed, no traffic has to be
sampled, and no consumer has to be enumerated — which is why the
verdict costs seconds and holds up in a merge gate.

The price of that independence is that the reading tells you what you
did, not what it will cost. Those are different questions, and the
sensor only answers the first one:

- A **breaking** change with nobody on the other end is still correctly
  classified breaking. It is also free to ship. The diff cannot tell
  the two situations apart, because the answer isn't in the diff.
- A **non-breaking** change can still break every caller — flip a
  default, tighten a validation rule, start returning results in a
  different order. The shape held, so the check is silent, and it is
  silent correctly: nothing about the contract changed.

For the second question — what does this cost, and who does it cost —
go elsewhere. [Contract tests](contract-tests.html) catch the
behavioral breaks that leave the shape intact. Consumer telemetry
says who is actually out there: the package index for a library,
per-endpoint and per-field traffic for a service.

## Response playbook

When the check reports a breaking change:

1. **Go find out who is on the other end.** The check has told you the
   change is incompatible. It has not told you whether that is
   expensive, and it cannot — that answer lives in traffic telemetry
   and the package index, not in the diff.
2. **If consumers exist, make it additive.** Ship the new surface
   alongside the old, migrate callers, and remove the old surface
   only after the telemetry confirms nobody is left.
3. **If removal is forced, version it.** A major-version bump or a
   `/v2` prefix is the honest signal to consumers; a silent removal
   is not.
4. **Automate the check as a merge gate.** A reviewer scanning a large
   diff misses a widened parameter or a field quietly made required;
   the tool compares every signature every time and does not get
   bored.

## How it gets gamed

- **Deprecation without removal.** Marking a surface deprecated and
  never deleting it. Nothing is ever classified breaking because
  nothing is ever removed, and the compatible surface grows until it
  is the thing nobody can change.
- **Break it semantically instead of structurally.** Change what a
  field *means*, or what an error code implies, while leaving every
  type where it was. The gate has nothing to say, and it is not wrong
  — it was asked about shape. But a team that knows this can route
  around the gate on purpose. [Contract
  tests](contract-tests.html) are the sensor that notices.
- **Version-bump laundering.** Reclassifying a breaking change as a
  "platform migration" so the compatibility gate does not run on
  it.

The meta-signal is how much of the public surface the check can
actually see. Anything not described by a spec or a signature the tool
parses — a hand-rolled endpoint, an undocumented header, a field added
by a serializer at runtime — produces no verdict at all, and silence
from a compatibility check reads exactly like a pass.

## What it cannot detect

API compatibility checks the *shape* of the interface, not the
*behavioral meaning*. A response with the same fields and types but
different semantics will pass compatibility checks.
