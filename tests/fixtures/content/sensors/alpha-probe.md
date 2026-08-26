---
id: SO-T01
title: Alpha Probe
family: structural
family_num: 1
oracle: high
oracle_note: the probe answers yes or no with no interpretation needed
independence: maximum
independence_note: written by a party with no stake in the answer
scope: module
latency: seconds
actionability: blocking
actionability_note: names the exact declaration that failed
type: predictive
type_note: it runs before anything ships
stack_level: compilation
categories:
- Structural
- Fixture Only
see_also:
- SO-T02
- behavioral
- atlas
last_reviewed: '2025-01-15'
references:
- title: A Fixture Publication With Every Field
  year: 2001
  tier: I
  url: https://example.invalid/fixture-publication
  kind: publication
  authors: A. Fixture, B. Fixture
  venue: FIXCON 2001
- title: A Fixture Publication With No URL
  year: 1999
  tier: IV
  kind: publication
  authors: C. Fixture
- title: fixturelint
  url: https://example.invalid/fixturelint
  kind: tool
  description: A tool reference, rendered under Tooling
- title: fixturefmt
  kind: tool
  description: A tool reference with no URL
- title: A Fixture Blog Post
  url: https://example.invalid/fixture-blog
  kind: blog
  year: 2018
- title: A Fixture Book
  kind: book
  year: 1975
- title: A Fixture Specification
  url: https://example.invalid/fixture-spec
  kind: spec
- title: A Fixture Reference Of Kind Other
  kind: other
---

Alpha Probe is a fixture entry. It exists to exercise the reference renderer
with one reference of every declared `kind`, so that a change to the
Publications / Tooling / Further reading bucketing shows up as a golden diff
rather than as something a human notices six months later.

It also carries a `see_also` of each resolvable shape: a sensor id
(`SO-T02`), a family slug (`behavioral`), and the literal `atlas`.

The body links to [the catalog](catalog.html) and to [Beta
Signal](beta-signal.html) by bare filename, which is the form
`fix_link_depths` rewrites to site-absolute URLs. It also carries the shapes
that rewriter must leave alone: an
[absolute URL](https://example.invalid/left-alone), an
[in-page anchor](#references), a <a class="wikilink" href="/atlas/">raw anchor
that already has a class</a>, and a [relative link to nothing in
particular](no-such-page.html) that is deliberately left for the link checker
to flag rather than silently rewritten.

Its `last_reviewed` is deliberately more than twelve months before the
catalog's own reference date, so the sidebar renders the stale flag.
