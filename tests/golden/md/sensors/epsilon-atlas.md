---
id: SO-T05
title: Epsilon Atlas Anchor
family: test-effectiveness
family_num: 3
oracle: minimum
oracle_note: it reports what happened, not whether that was correct
independence: minimum
independence_note: it measures the very suite that produced it
scope: user-journey
latency: weeks
actionability: exploratory
type: retrospective
type_note: it can only speak about runs that already happened
stack_level: mutation-testing
categories:
- Test Effectiveness
- Fixture Only
see_also:
- atlas
- structural
- SO-T04
last_reviewed: '2026-03-02'
---

A short opening paragraph, under the blurb limit, so the untruncated branch
of the blurb extractor is exercised too.

Epsilon Atlas Anchor exists so the fixture corpus spans four families and
four stack levels, which is what gives the atlas grid, the family pages, the
categories page and the dependency graph something to render.

## Notes

It shares `last_reviewed` with Beta Signal and differs from Alpha Probe and
Delta, so `review_dates_discriminate` is true for this corpus and the
homepage takes its real-ordering branch rather than the degenerate one.

## Notes

A second heading with the same text, so the heading-id de-duplicator has a
collision to resolve.
