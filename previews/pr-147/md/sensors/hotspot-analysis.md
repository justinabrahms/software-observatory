---
id: SO-008c
title: Hotspot Analysis
family: architecture
family_num: 08
oracle: low
oracle_note: a hotspot is a risk indicator, not a bug
independence: high
independence_note: computed from git and metrics
scope: module
latency: minutes
actionability: exploratory
actionability_note: shows the heat map
type: retrospective
stack_level: static-analysis
categories:
- Architecture
see_also:
- SO-008
- SO-008b
- SO-008d
- SO-012d
- evolution
references:
- title: A Novel Approach for Estimating Truck Factors
  year: 2016
  tier: II
  url: https://arxiv.org/pdf/1604.06766
  kind: publication
  authors: Guilherme Avelino, Leonardo Passos, Andre Hora, Marco Tulio Valente
  venue: arXiv 1604.06766 (companion to ICPC 2016)
- title: Don't Touch My Code! Examining the Effects of Ownership on Software Quality
  year: 2011
  tier: II
  url: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/bird2011dtm.pdf
  kind: publication
  authors: Christian Bird, Nachiappan Nagappan, Brendan Murphy, Harald Gall, Premkumar Devanbu
  venue: ESEC/FSE '11
- authors: Adam Tornhill
  title: Your Code as a Crime Scene
  year: 2015
  kind: publication
  tier: IV
- title: CodeScene
  kind: tool
  url: https://codescene.com
  description: Code analysis predicting technical debt from behavioral code
- title: git-quick-stats
  kind: tool
  url: https://github.com/arzzen/git-quick-stats
  description: Git history analysis script
---

Change frequency times complexity. Identifies places where the system is
simultaneously *difficult* and *frequently changed* — more interesting than
"files with the most lines."

Hotspot analysis combines two signals: how complex a module is
(cyclomatic complexity, nesting depth) and how often it changes (commit
frequency). The intersection — a complex module that changes frequently — is
where risk concentrates.

## In practice

The reading is a ranked list: modules scored by change frequency weighted
against complexity, usually over the last 6 to 12 months.

```text
window: 12 months, complexity = cyclomatic

  rank  module                     commits  complexity  authors
  1     src/checkout/session.py    187      42          9
  2     src/billing/pricing.py     141      38          4
  3     lib/feature_flags/rules.ts 96       29          7
  4     src/checkout/session.py (again, 3 of top 10 commits
        are merge-conflict fixes)
```

Reading it well:

1. **Rank is a question, not a verdict.** A top hotspot means "look
   here first," not "this code is broken." Some hotspots are healthy
   and churning because the product churns there.
2. **Cross-reference with defects.** A hot module that also appears in
   recent incident reports and [escaped
   defects](escaped-defect-rate.html) is where attention pays back; a
   hot module with a clean record may just be popular.
3. **Watch the author column.** Nine authors in one file is a
   coordination problem independent of complexity.
4. **Compare windows.** A module that was cold six months ago and is
   hot now marks a behavior change, which is often more interesting
   than the perennial top ten.

## How it gets gamed

- **Squash to shrink the count.** If hotspot ranking drives attention
  or blame, committing in large squashed batches lowers the apparent
  change frequency without changing the churn.
- **Touch it to cool it.** A few cosmetic commits in a quiet module
  raise its frequency and dilute the ranking; conversely, routing real
  changes through a side branch keeps a hot file artificially cold.
- **Rename and split to reset history.** File moves restart the clock
  in tools that do not track renames, demoting a hotspot without
  touching its content.
- **Complexity theater.** Wrapping a gnarly function in three small
  ones lowers the per-function score while the tangled logic moves one
  level down unchanged.

The meta-signal is churn per author: a hotspot whose commits concentrate
on one person is a knowledge problem the ranking alone will not show.

## Response playbook

When a hotspot keeps churning:

1. **Read the churn, not the code.** Run the git log for the module and
   ask what each change was actually for. Repeated changes for the same
   reason are the specification of the missing abstraction.
2. **Test before touching.** A hot, complex module is exactly where an
   untested refactor causes incidents. Establish [example-based
   tests](example-based-tests.html) around current behavior first.
3. **Extract one seam.** Do not rewrite. Find the axis the churn keeps
   crossing (a config knob, a policy switch, a format conversion) and
   pull it out so the next change does not touch the core.
4. **Pair the next three changes.** If nine authors churn one file,
   route the next edits through review with the person who knows it,
   and write down what they explain.
5. **Re-score after a quarter.** The hotspot list is cheap to recompute;
   a fix that worked shows up as a rank drop.

## What it cannot detect

Hotspot analysis doesn't tell you *why* a module changes frequently or
*whether* it's correct. It identifies where attention is needed, not what
the attention should fix.
