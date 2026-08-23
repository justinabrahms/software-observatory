---
id: SO-010
title: Independent Review
family: comprehension
family_num: '10'
oracle: medium
oracle_note: 'subjective, but disagreement is signal'
independence: medium
independence_note: 'reviewer is independent of author'
scope: module
latency: hours
actionability: guiding
actionability_note: 'reviewer asks "what does this do?"'
type: predictive
stack_level: static-analysis
categories:
- Comprehension
- Epistemic Accessibility
see_also:
- SO-010b
- SO-010c
- SO-010d
last_reviewed: 2026-08-23
references:
- title: An Empirical Study on the Effectiveness of Security Code Review
  year: 2013
  tier: I
  url: https://people.eecs.berkeley.edu/~daw/papers/coderev-essos13.pdf
  kind: paper
- title: 'The Cost of Interrupted Work: More Speed and Stress'
  year: 2008
  tier: I
  url: https://ics.uci.edu/~gmark/chi08-mark.pdf
  kind: paper
- authors: Fagan
  title: Design and Code Inspections to Reduce Errors
  year: 1976
  kind: paper
- title: GitHub PR review
  kind: tool
  url: https://docs.github.com/pull-requests
  description: Pull request review on GitHub
- title: Gerrit
  kind: tool
  url: https://www.gerritcodereview.com
  description: Web-based code review for Git
- title: Reviewable
  kind: tool
  url: https://reviewable.io
  description: Code review tool for GitHub PRs
---

Can another engineer explain what this does? A sensor of *epistemic
accessibility* — if humans can't understand the system, that's itself a
correctness risk.

Independent review is the oldest comprehension sensor: someone who didn't
write the code reads it and attempts to explain its behavior. Disagreement
between author and reviewer reveals implicit assumptions, missing context,
and unclear logic.

## In practice

A reading is the review itself: a verdict plus the questions and
objections that produced it. A healthy one looks like this:

- **Verdict:** changes requested
- **Blocking:** `retry_backoff()` doubles past the 30 s cap because the
  cap is checked before the multiply, not after. Reproduce with six
  retries from a cold start.
- **Question:** the migration drops `orders.legacy_id`, but the
  exporter in `batch/ship.py` still reads it. Which change lands
  first?
- **Note:** this function now does retry and rate limiting; consider
  splitting it before the next change builds on it.

The blocking item is a falsifiable claim about behavior, the question is
a dependency the reviewer could not verify alone, and the note is a
design smell. Together they show the reviewer actually read the change.

Reading a review well:

- **Judge by the specificity of the objections.** "Looks good" is not
  a reading. A review that names functions, inputs, and failure modes
  is doing the work; one that comments only on formatting is not.
- **Disagreement is the signal, not the noise.** When author and
  reviewer disagree about what the code does, at least one of them
  holds a wrong model. That gap is what the sensor exists to find.
- **Ask what the reviewer checked against.** A review of the diff
  alone misses what the diff breaks elsewhere. Strong reviews quote
  the caller, the schema, or the spec, not just the changed lines.

## How it gets gamed

Review is a human gate, which makes it the easiest to pass without
doing the work:

- **Rubber-stamp.** Approve within seconds of being asked, every
  time. Time from review request to approval, tracked per reviewer,
  exposes it: a reviewer who approves a 40-file diff in 90 seconds
  read nothing.
- **Diff-only review.** Reading the changed lines without the callers
  they break finds nothing in code that was already broken upstream.
  The review passes because the review never opened the rest of the
  system.
- **Courtesy approval.** Reviewers approve because the author is
  senior, in a hurry, or on a deadline. The approval tracks the
  author, not the change.
- **Flooding.** A 3,000-line change guarantees nothing gets read.
  Size is the cheapest gaming move available: no rule is broken, and
  no review is possible.

The meta-signal is approval rate and time-to-approve per reviewer. A
reviewer who approves everything, instantly, is a sensor that always
reports green.

## Response playbook

When a review flags the change:

1. **Reproduce blocking findings before arguing.** If the reviewer
   names a failure mode, run it. A finding that reproduces is not a
   matter of opinion; a finding that does not needs a test, not a
   rebuttal.
2. **Answer questions with evidence, not intent.** "That column is
   unused" deserves a grep across the codebase, not "I think we
   removed the last reader." If the reviewer could not verify it,
   verify it for them.
3. **Split a change that attracts only formatting comments.** A
   review that found nothing substantive in a 2,000-line diff almost
   certainly read nothing substantive. Small changes get real
   reviews; large ones get approvals.
4. **Record the disagreement, not just the verdict.** When author and
   reviewer disagree about what the code does, write down both
   interpretations. One of them is wrong, and the record is how the
   next reader finds out which.
5. **Do not merge over an unresolved objection.** An objection the
   author talked the reviewer out of, without evidence, is a finding
   that escaped. The merge button is not an argument.

## What it cannot detect

Review quality varies enormously with reviewer expertise, attention, and
time. A rubber-stamp review provides no signal. Also, review can't catch
problems in code the reviewer doesn't read carefully.
