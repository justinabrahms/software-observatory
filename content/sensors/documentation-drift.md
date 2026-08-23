---
id: SO-010b
title: Documentation Drift
family: comprehension
family_num: "10"
oracle: low
independence: high
scope: module
latency: days
actionability: exploratory
type: retrospective
stack_level: static-analysis
categories:
  - Comprehension
  - Documentation
see_also:
  - SO-010
  - SO-010c
  - SO-010d
last_reviewed: 2026-08-23
---

Does documentation still predict behavior? A sensor of the gap between what
the system is documented to do and what it *actually* does.

Documentation drift measures whether the docs match reality. When they
diverge, the documentation becomes a liability: it misleads rather than
guides. Detecting drift requires comparing documented behavior to
[observed behavior](observability-events.html) or [test
assertions](example-based-tests.html).

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

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Low — drift is a risk factor, not a bug |
| Independence | High — docs and code are independent artifacts |
| Scope | Module-level |
| Feedback latency | Days |
| Actionability | Exploratory — shows the gap |
| Type | Retrospective |

## What it cannot detect

Documentation drift can only be detected where documentation exists.
Undocumented behavior is invisible to this sensor.

## Tooling

- doctest
- rustdoc
- TypeDoc
- OpenAPI round-trip

## References

- A First Look at the Deprecation of RESTful APIs: An Empirical Study (2020, tier II) — https://arxiv.org/abs/2008.12808

- https://docs.python.org/3/library/doctest.html