---
id: SO-010b
title: Documentation Drift
family: comprehension
family_num: '10'
oracle: low
oracle_note: drift is a risk factor, not a bug
independence: high
independence_note: docs and code are independent artifacts
scope: module
latency: days
actionability: exploratory
actionability_note: shows the gap
type: retrospective
stack_level: production-behavior
categories:
- Comprehension
see_also:
- SO-010
- SO-010c
- SO-010d
last_reviewed: '2026-08-24'
references:
- title: 'A First Look at the Deprecation of RESTful APIs: An Empirical Study'
  year: 2020
  tier: II
  url: https://arxiv.org/abs/2008.12808
  kind: publication
  authors: Jerin Yasmin, Yuan Tian, Jinqiu Yang
  venue: arXiv 2008.12808
- title: doctest
  kind: tool
  url: https://docs.python.org/3/library/doctest.html
  description: Python doctest module
- title: rustdoc
  kind: tool
  url: https://doc.rust-lang.org/rustdoc
  description: Rust documentation generator with doc tests
- title: TypeDoc
  kind: tool
  url: https://typedoc.org
  description: TypeScript API documentation generator
- title: OpenAPI round-trip
  kind: tool
  url: https://editor.swagger.io/
  description: Validate OpenAPI spec against actual API responses
---

Does documentation still predict behavior? A sensor of the gap between what
the system is documented to do and what it *actually* does.

Documentation drift measures whether the docs match reality. When they
diverge, the documentation becomes a liability: it misleads rather than
guides. Detecting drift requires comparing documented behavior to
[observed behavior](observability-events.html) or [test
assertions](example-based-tests.html).

## In practice

A drift reading is a list of documented claims checked against executable
reality: doctests that fail, spec round-trips that mismatch, prose checked
against observed behavior. From a docs audit of a payments library:

| Doc location | Claim | Reality | Status |
|--------------|-------|---------|--------|
| README quickstart | `client.charge(amount)` | method renamed to `create_charge` | DRIFT |
| doctest, refund guide | refund returns `Refund` object | returns a dict since v3.2 | DRIFT |
| OpenAPI spec, /v1/payouts | 200 with `eta` field | field removed 8 months ago | DRIFT |
| runbook: failover | manual DNS switch | automated since March | stale but harmless |

Reading it well:

1. **Prioritize by consequence.** A drifted runbook gets someone paged
   at 3 a.m. following wrong steps; a stale README example costs a
   newcomer an afternoon. Rank fixes by who trusts the doc under
   pressure.
2. **Distinguish stale from wrong.** A doc describing removed behavior
   misleads; a doc that merely lags the style guide only annoys. The
   first is a correctness bug in the documentation.
3. **Executable docs drift loudly, prose drifts silently.** The doctest
   failure is the cheap signal; the audit above is the expensive one,
   and the two lists should not diverge for long.
4. **Date the claims.** Docs with a "verified against v3.4" stamp make
   drift measurable; undated prose is unfalsifiable.

## How it's measured

Drift is only *sensorable* when documentation is executable or generated:

- **Doctests** (Python `doctest`, Rust doc tests) — code in docs that's
  run as a test. If the docs drift, the test fails.
- **Executable specs** — OpenAPI round-trip validation (does the schema
  match the actual responses?), JSON Schema validation of examples,
  Cucumber/Gherkin behavior specs.
- **Generated docs** — rustdoc, godoc, TypeDoc where the docs are extracted
  from the code itself. Drift is structurally impossible when the code *is*
  the source of the docs.

Prose docs drift silently and can only be caught by
[independent review](independent-review.html) or by comparing documented
behavior to [observed behavior](observability-events.html).

## How it gets gamed

- **Rubber-stamp updates.** A drift checker flags a doc, someone bumps
  its "last verified" date without reading it, and the metric goes
  green while the doc still lies.
- **Delete what you cannot fix.** Removing a stale page clears the
  finding; if the deleted content was load-bearing, the knowledge is
  now tribal.
- **Doctest theater.** Rewriting an executable example to assert
  almost nothing (`>>> client.ping()` ... `True`) keeps the test green
  forever while documenting nothing.
- **Move the truth elsewhere.** The README stops drifting because all
  real information moved to an unwritten wiki page the checker never
  sees.

The meta-signal is doc-edit content: updates that change a timestamp or
"verified" stamp without changing prose are the tell.

## Response playbook

When the drift audit reads badly:

1. **Fix, delete, or mark stale, in that order.** Every flagged doc
   gets one of three outcomes this week. A doc nobody will fix should
   say "unverified since v3" at the top, not sit silently wrong.
2. **Make the highest-traffic docs executable.** Convert the quickstart
   and the top three API examples into doctests or spec round-trips so
   future drift fails CI instead of waiting for an audit.
3. **Generate instead of writing.** Where the doc restates signatures,
   schemas, or config shapes, switch to generated output from the code
   and delete the hand-maintained copy.
4. **Attach docs to the change that breaks them.** Require any PR that
   changes documented behavior to touch the corresponding doc in the
   same commit; review then catches drift at birth.
5. **Re-run the audit on a schedule.** Quarterly is usually enough; the
   point is that the number moves, not that it is zero.

## What it cannot detect

Documentation drift can only be detected where documentation exists.
Undocumented behavior is invisible to this sensor.
