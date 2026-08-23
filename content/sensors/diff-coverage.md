---
id: SO-003b
title: Diff Coverage
family: test-effectiveness
family_num: 3
oracle: low
oracle_note: 'execution ≠ correctness'
independence: medium
independence_note: 'the test author writes the tests'
scope: diff
scope_note: 'change-scoped'
latency: minutes
actionability: guiding
actionability_note: 'shows exactly which changed lines lack coverage'
type: predictive
type_note: 'catches untested changes before deployment'
stack_level: behavioral-tests
categories:
- Test Effectiveness
- Change
- Coverage
- Agentic Coding
see_also:
- SO-003
- change-family
- ai-sensors
last_reviewed: 2026-08-23
references:
- title: State of Mutation Testing at Google
  year: 2018
  tier: III
  url: https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/46584.pdf
  kind: paper
- title: diff-cover
  kind: tool
  url: https://github.com/Bachmann123/diff-cover
  description: Coverage for changed lines only
- title: Codecov
  kind: tool
  url: https://about.codecov.io
  description: Hosted code coverage reporting
- title: Coveralls
  kind: tool
  url: https://coveralls.io
  description: Hosted code coverage reporting
---

You don't necessarily care whether some 15-year-old module has 43% coverage.
You care: *did the code I just changed have evidence attached to it?*

## The question that matters for agentic coding

Diff coverage is extremely useful for [agentic coding](catalog.html#ai-sensors).
The question isn't "is the codebase healthy?" It's:

```
"What changed, and what evidence do we have
 that the change didn't damage anything?"
```

Diff coverage answers the narrowest version: of the lines added or modified
in this diff, how many were executed by the test suite? It's a weak oracle
— execution is not correctness — but it's a sensor that the code that was
just written has *any* evidence attached to it at all.

> Diff coverage is the minimum viable sensor for change. It doesn't tell you
> the change is correct. It tells you the change was *exercised*. That's a
> necessary — though not sufficient — condition for believing the tests
> provide evidence about it.

## The hierarchy

Diff coverage sits at the intersection of test effectiveness and change
sensors:

```
line coverage      → did this line execute?
diff coverage       → did the CHANGED lines execute?
mutation testing    → would we catch a wrong impl?
```

## In practice

A diff coverage reading appears in CI as a check on the change, scoped to
the lines this diff touched rather than the whole repository:

```
diff-cover report
-------------
Total:   42 lines changed, 29 covered (69%)
Threshold: 80%  FAIL

Uncovered lines:
  billing/invoice.py (4 lines): 112, 113, 141, 142
  billing/tax.py (9 lines): 30-38
```

The verdict is pass or fail against a threshold set on changed lines
only, which is what makes it readable at review time. Reading it well:

1. **The uncovered-line list is the review comment.** Each listed line
   is a question to the author: what test exercises this? If the answer
   is none, that is the gap, and it is smaller and more concrete than
   any repository-wide number.
2. **A high total with a failing diff means the change is the problem.**
   The rest of the codebase being well covered does not excuse new code
   arriving with no evidence. The diff is the only number that matters
   in review.
3. **Watch for churn lines inflating the denominator.** Reformatted or
   regenerated files can drown the real change in covered noise. Scope
   the report to the meaningful diff when that happens.
4. **Remember what passing means.** Covered lines executed; they were
   not necessarily asserted on. Diff coverage is the floor, and
   [mutation testing](mutation-testing.html) is the next sensor up.

## How it gets gamed

Because the gate only looks at changed lines, it can be satisfied cheaply:

- **Assertion-free tests on the diff.** The fastest way to turn changed
  lines green is a test that calls the new code and asserts nothing. The
  gate passes; the change still has no evidence. This is the agentic
  version of the failure: a model told to raise diff coverage will
  generate exactly these tests unless asked to kill mutants too.
- **Splitting the change.** Moving new logic into a file marked
  generated, vendored, or excluded keeps it out of the denominator.
  Same trick: land untested code in a separate commit that the coverage
  tool ignores by configuration.
- **Threshold shopping.** When the gate fails, the argument becomes
  "80% is too strict for this module," and the threshold drops. Every
  lowering is a one-way ratchet that makes the next change easier to
  land without evidence.

The meta-signal is the mutation score of the diff. Diff coverage without
it measures attendance, not attention.

## Response playbook

When a diff coverage gate fails or a change lands untested:

1. **List the uncovered lines and map each to a test.** For every line
   in the report, name the test that should exercise it. If no test
   exists, write one, asserting on the line's output rather than its
   execution.
2. **Reject changes that lower diff coverage.** Send the change back
   with the uncovered lines quoted in the review comment. A concrete
   line list is harder to argue with than a percentage.
3. **Fix the exclusion config before the code.** If the gap comes from
   files excluded by pattern, decide explicitly whether that exclusion
   is still right. Silent exclusions are where untested changes hide.
4. **Pair the gate with a stronger oracle.** Once diff coverage passes,
   run [mutation testing](mutation-testing.html) on the changed code to
   check whether the new tests would catch a wrong implementation.

## What it cannot detect

Diff coverage cannot tell you whether the tests that *ran* the changed code
actually *asserted* anything about its correctness. A line can execute
without any test verifying its output. It also says nothing about
[untested behavior](mutation-testing.html) that the tests don't cover.
