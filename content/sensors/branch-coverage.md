---
id: SO-003c-b
title: Branch Coverage
family: test-effectiveness
family_num: '03'
oracle: low
oracle_note: execution is not correctness
independence: low
independence_note: same author writes tests
scope: function
latency: seconds
actionability: guiding
actionability_note: shows which branches weren't exercised
type: predictive
stack_level: behavioral-tests
categories:
- Test Effectiveness
- Coverage
see_also:
- SO-003c
- SO-003
- SO-003b
last_reviewed: '2026-08-24'
references:
- title: Coverage Is Not Strongly Correlated with Test Suite Effectiveness
  year: 2014
  tier: I
  url: https://www.cs.ubc.ca/~rtholmes/papers/icse_2014_inozemtseva.pdf
  kind: publication
  authors: Laura Inozemtseva, Reid Holmes
  venue: ICSE 2014
- title: coverage.py
  kind: tool
  url: https://coverage.readthedocs.io
  description: Python code coverage measurement
- title: Istanbul
  kind: tool
  url: https://istanbul.js.org
  description: JavaScript code coverage
- title: JaCoCo
  kind: tool
  url: https://www.jacoco.org
  description: Java code coverage
- title: gcov
  kind: tool
  url: https://gcc.gnu.org/onlinedocs/gcc/Gcov.html
  description: GCC code coverage
---

Did we exercise both sides of decisions? Better than [line
coverage](line-coverage.html). Path coverage is better still, but usually
expensive and impractical at scale.

Branch coverage catches the case where a conditional's true path is tested
but the false path is not — a common gap that line coverage misses because
the line containing the branch executes either way.

## In practice

A branch coverage reading is a summary line per file, usually rendered by
the same tool that measures [line coverage](line-coverage.html), with two
extra columns for decision points:

```
Name                        Stmts   Miss  Branch  BrPart  Cover
billing/invoice.py          214     31      88      14    79%
billing/tax.py               96      3      42       2    95%
TOTAL                       310     34     130      16    83%
```

`BrPart` is the interesting number: branches that executed on one side
only. Reading it well:

1. **Read partial branches as a to-do list.** Every entry in the BrPart
   column is a decision whose other side has never run. That is the
   specific, addressable gap, and it is what line coverage cannot show.
2. **Open the annotated source, not just the summary.** Coverage tools
   mark the exact line where one side of a conditional never fired. The
   summary percentage hides this; the annotation is the actionable part.
3. **Treat low branch coverage on error paths as a finding.** Untested
   `else` arms on validation and failure handling are where production
   surprises live, and they are the first place to spend new tests.
4. **Do not chase 100%.** The last few percent measure defensive code
   that cannot be reached without contrivance, and the tests written to
   reach it usually assert nothing.

## How it gets gamed

Branch coverage counts execution, so it can be manufactured with
execution:

- **Assertion-free tests.** A test that calls a function with inputs
  chosen to walk both sides of every conditional moves the branch number
  without verifying anything. The metric rises; the oracle does not.
  [Mutation testing](mutation-testing.html) exposes this quickly: padded
  suites let most mutants through.
- **Garbage inputs for defensive branches.** Feeding malformed data into
  a parser exercises its error arms and counts as coverage, even though
  no test states what the parser should do with the input.
- **Exclusion pragmas.** `# pragma: no cover` and equivalent annotations
  quietly remove inconvenient branches from the denominator. A growing
  exclusion list is coverage authority being spent, the same pattern as
  lint suppressions in a [linter](linter.html).

The meta-signal is the mutation score restricted to covered branches. If
branch coverage climbs while it falls, the new tests are tourism.

## Response playbook

When branch coverage drops or a report shows a gap worth closing:

1. **Find the uncovered branch in the annotated report.** Open the source
   annotation and locate the decision whose missing side is flagged. Do
   not write a test from the percentage alone.
2. **Write the test for the missing side first.** The untested arm is
   the specification: construct the input that takes it, and assert on
   the outcome, not merely that the code ran.
3. **Delete unreachable branches.** If the missing arm is dead code,
   remove it. A branch that cannot execute is not coverage waiting to
   happen; it is clutter that dilutes the reading.
4. **Send back changes that drop coverage.** If a drop is concentrated
   in one change, return it with the specific uncovered branches named.
   A blanket "add tests" instruction produces the padding above.

## What it cannot detect

Same limitations as [line coverage](line-coverage.html) — execution is not
assertion. Branch coverage tells you the branch ran, not that the right
thing happened when it did.
