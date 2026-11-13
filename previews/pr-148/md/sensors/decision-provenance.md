---
id: SO-010d
title: Decision Provenance
family: comprehension
family_num: '10'
oracle: low
oracle_note: missing provenance is a risk factor
independence: low
independence_note: the author of the change writes its own record
scope: module
latency: days
actionability: exploratory
actionability_note: shows whether provenance exists
type: retrospective
stack_level: static-analysis
categories:
- Comprehension
see_also:
- SO-010
- SO-010b
- SO-010c
last_reviewed: '2026-09-03'
references:
- authors: Michael Nygard
  title: Documenting Architecture Decisions
  year: 2017
  kind: publication
  tier: IV
- title: ADRs
  kind: tool
  url: https://adr.github.io
  description: Architecture Decision Records
- title: Conventional Commits
  kind: tool
  url: https://www.conventionalcommits.org
  description: Structured commit message specification
- title: git blame
  kind: tool
  url: https://git-scm.com/docs/git-blame
  description: Git history annotation per line
---

Can you answer "why is this weird thing here?" A sensor of *archaeological
accessibility* — can you determine why code exists, not just what it does?

Decision provenance traces the history of a design decision: the ADRs, PRs,
discussions, and constraints that led to the current code. When provenance
is lost, the code becomes untouchable — nobody knows whether it can be
changed safely.

This sensor scores low on independence, which is unusual for something
read out of history. `git blame` and `git log -S` are not manipulable —
they report when a line changed and who changed it, and no amount of
intent rewrites that. But those are not the questions being asked. The
"why" lives in prose written by the author of the change, at the same
time as the change, reviewed by nobody with an interest in
contradicting it. Every entry under "How it gets gamed" below is that
one weakness in a different costume, which is why provenance is graded
on what it explains rather than counted.

## In practice

The reading is an attempted reconstruction: pick a line of code that
looks wrong, and trace how far back the "why" survives. A real attempt
on one suspicious rounding rule:

```text
$ git blame -L 412,412 src/billing/pricing.py
9f3c2ab (dana 2023-06-14) rate = round_half_even(rate, 6)

$ git log -S round_half_even --oneline -- src/billing/pricing.py
9f3c2ab fix: banker's rounding for cross-border rates
1b7e0aa initial pricing module

$ git show 9f3c2ab --stat | tail -1
 3 files changed, 9 insertions(+), 2 deletions(-)

$ ls docs/adr/ | grep -i round
(no match)
```

| Question | Source checked | Answer found |
|----------|----------------|--------------|
| What does this line do? | code | yes |
| When did it change? | git log | yes |
| Why banker's rounding? | commit subject only | partial |
| What was rejected instead? | nowhere | no |
| Is the reason still valid? | nobody knows | no |

Reading it well:

1. **Provenance is a gradient, not a bit.** "Commit subject says why"
   is weak provenance; an ADR with rejected alternatives is strong.
   Grade what you find, do not score it binary.
2. **The reconstruction is the measurement.** If it took an hour of
   digging and three tools to answer one why-question, that cost is
   the reading, and every future change to this code pays it again.
3. **Follow links in both directions.** An ADR that nobody links from
   the code is as good as missing; a comment that names its ADR is the
   whole point.
4. **Age matters.** Provenance answers why code was added; a separate
   question is why it is still there. Old records need re-justification.

## How it's recorded

- **ADRs** (Architecture Decision Records, Michael Nygard's pattern) —
  short documents capturing context, decision, and consequences. The
  canonical technique.
- **Commit conventions** — linking commits to issues, explaining *why*
  not just *what* (Conventional Commits, referencing tickets).
- **`git blame` / `git log -S`** — the fallback when no explicit provenance
  was recorded. The archaeology tool of last resort.

Provenance decays — an ADR from three years ago may explain why the code
was *added* but not why it's *still there*. Periodic re-justification keeps
provenance alive.

## How it gets gamed

- **Retroactive ADRs.** The decision is made, shipped, and debated; the
  ADR is written weeks later to justify what already exists. The record
  reads clean, but its context section is rationalization and its
  alternatives were never seriously weighed.
- **Template-filler records.** "Context: we needed a queue. Decision:
  use Kafka." An ADR that fills every section while saying nothing
  passes any count-based dashboard and explains nothing.
- **Record far from the code.** The decision lives in a wiki, a deck,
  or a channel the code never links to; provenance technically exists
  and is practically unrecoverable.
- **Squash away the discussion.** Squash-merging a long debate into a
  one-line commit deletes the very record this sensor reads; the PR
  body becomes the sole artifact, and it is rarely written for
  archaeologists.

The meta-signal is the rejected-alternatives section: ADRs with none
were almost certainly written after the decision.

## Response playbook

When a reconstruction attempt comes back empty:

1. **Exhaust the artifacts before asking a person.** `git blame`,
   `git log -S`, linked tickets, and PR search take twenty minutes and
   sometimes beat tribal memory.
2. **Ask the author, then write it down.** If the answer lives in a
   person's head, capture it as an ADR or a code comment the same day;
   otherwise the next dig pays the full cost again.
3. **Mark the gap explicitly.** If nobody knows why the code is there,
   say so at the site: "reason lost, do not change without re-deriving
   the invariant." An honest unknown beats a confident guess.
4. **Require the why at the gate.** PR templates that demand a linked
   ticket or rationale, enforced in review, stop new gaps from forming
   at zero cost.
5. **Re-justify old ADRs periodically.** Walk the ADR log once a year;
   each record gets reaffirmed, superseded, or retired. Provenance
   that is never revisited rots into mythology.

## What it cannot detect

Decision provenance can only exist where decisions were *recorded*. Decisions
made verbally, in deleted branches, or in private messages are invisible to
this sensor.
