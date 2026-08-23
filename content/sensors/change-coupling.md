---
id: SO-009b
title: Change Coupling
family: evolution
family_num: 09
oracle: medium
oracle_note: 'coupling correlates with risk'
independence: high
independence_note: 'computed from git history'
scope: system
latency: days
actionability: exploratory
actionability_note: 'shows the coupling clusters'
type: retrospective
stack_level: static-analysis
categories:
- Evolution
- Hidden Coupling
- Black-Box Sensors
see_also:
- SO-009
- SO-009c
- SO-009d
- SO-008
last_reviewed: 2026-08-23
references:
- title: Organizational Volatility and its Effects on Software Defects
  year: 2010
  tier: II
  url: https://mockus.org/papers/orgQuality-slides.pdf
  kind: paper
- title: 2017 State of DevOps Report
  year: 2017
  tier: II
  url: https://dora.dev/research/2017/2017-state-of-devops-report.pdf
  kind: paper
- authors: Adam Tornhill
  title: Your Code as a Crime Scene
  year: 2015
  kind: paper
- title: CodeScene
  kind: tool
  url: https://codescene.com
  description: Code analysis predicting technical debt from behavioral code
- title: git-quick-stats
  kind: tool
  url: https://github.com/arzzen/git-quick-stats
  description: Git history analysis script
---

Which files repeatedly change together? A sensor of *hidden coupling* — the
repository itself becomes a sensor, no code reading required.

Change coupling reveals relationships the [dependency
graph](dependency-graph.html) can't see: modules that have no structural
dependency but always change together. This is often a sign of shared
business rules, duplicated logic, or implicit coordination.

## In practice

The reading is a co-change report over a window of history: pairs of
files that changed in the same commit more often than chance, ranked by
support and confidence.

```text
window: last 12 months, 1,842 commits

  files                          co-changes  confidence
  src/billing/pricing.py         27          90%
  src/billing/tests/test_pricing.py
                                 (24 of 27 pricing changes)
  web/cart/cart.ts               19          76%
  web/promotions/promo.ts        (15 of 19 cart changes, no import
                                 in either direction)
  api/orders/orders.go           11          69%
  db/migrations/*.sql            (9 of 11 order changes ship a
                                 migration)
```

Reading it well:

1. **Confidence beats raw count.** Twenty-seven co-changes mean little
   if the file changes two hundred times; 90% confidence means the two
   files are effectively one unit.
2. **The interesting pairs cross module boundaries.** Co-change inside
   one package is normal development; co-change across packages with no
   import edge is the hidden coupling this sensor exists to find.
3. **Filter the noise before believing it.** Formatting commits, bulk
   renames, and dependency bumps co-change everything with everything.
   Exclude them or the report is unreadable.
4. **Coupling is a question, not a verdict.** Each strong pair needs a
   human answer: shared business rule, duplicated logic, or coincidence
   of authorship.

## How it gets gamed

- **Split the commit.** An engineer who learns the tool watches for
  co-change can land the two halves of one logical change in separate
  commits, erasing the signal without removing the coupling.
- **Game the window.** The report only covers the last N months; a team
  can wait out the window or land noisy commits until the real pair
  drops off the ranking.
- **Bulk-change camouflage.** Committing a sweep of formatting or
  license-header edits across the repo dilutes every co-change count
  at once.
- **Rename to reset history.** File moves and renames break tracking in
  naive tools, restarting the clock on a pair that is still coupled.

The meta-signal is the stability of the ranking itself: a healthy report
churns slowly, while one being managed shows pairs appearing and
vanishing around review dates.

## Response playbook

When the co-change report shows strong hidden coupling:

1. **Pick the strongest cross-boundary pair and find the reason.** Read
   both files together; the shared business rule or duplicated logic is
   usually visible within an hour.
2. **Extract the shared rule.** If two files change together because
   they encode the same invariant, move that invariant into one place
   both files call.
3. **Add the missing structural edge.** Where the coupling is real and
   should stay, make it explicit: an import, a shared module, or a
   [contract test](contract-tests.html) so the next change cannot be
   half-done.
4. **Guard with a test before untangling.** Coupled files change
   together for a reason; capture the current joint behavior in an
   [integration test](integration-tests.html) first.
5. **Re-run the analysis after the refactor.** The pair should drop out
   of the ranking; if it does not, the fix missed the real coupling.

## What it cannot detect

Change coupling shows correlation, not causation. Files that change together
may do so for coincidental reasons (same sprint, same author) rather than
structural coupling.
