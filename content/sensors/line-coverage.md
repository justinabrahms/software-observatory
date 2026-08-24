---
id: SO-003c
title: Line Coverage
family: test-effectiveness
family_num: '03'
oracle: low
oracle_note: execution is not correctness
independence: low
independence_note: same author writes tests
scope: line
latency: seconds
actionability: guiding
actionability_note: shows which lines weren't executed
type: predictive
stack_level: behavioral-tests
categories:
- Test Effectiveness
- Coverage
see_also:
- SO-003c-b
- SO-003
- SO-003b
last_reviewed: '2026-08-24'
references:
- title: Coverage Is Not Strongly Correlated with Test Suite Effectiveness
  year: 2014
  tier: I
  url: https://www.cs.ubc.ca/~rtholmes/papers/icse_2014.pdf
  kind: paper
  authors: Laura Inozemtseva, Reid Holmes
  venue: ICSE 2014
- title: Does Mutation Testing Improve Testing Practices?
  year: 2021
  tier: I
  url: https://homes.cs.washington.edu/~rjust/publ/mutation_testing_practices_icse_2021.pdf
  kind: paper
  authors: Goran Petrović, Marko Ivanković, Gordon Fraser, René Just
  venue: ICSE 2021
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

Did we execute this line? Useful but weak. A project can have 90% line
coverage while [mutation testing](mutation-testing.html) finds large numbers
of mutations that tests don't detect.

Coverage measures execution. An assertion measures correctness. These are
not the same thing.

## In practice

A line coverage reading is the summary every coverage tool prints at the
end of a test run:

```
Name                         Stmts   Miss  Cover
api/handlers.py              342     58    83%
api/middleware.py             96      4    96%
TOTAL                        438     62    86%
```

The same report annotates the source, marking each uncovered line. A few
habits keep it honest:

1. **Read the uncovered lines, not the percentage.** The number is a
   summary; the annotated source is the finding. Ten uncovered lines in
   an error handler matter more than a 2-point total.
2. **Watch the trend, gate the delta.** Absolute coverage is mostly
   noise between projects. The useful readings are "did this change
   lower coverage" and "are the changed lines covered," which is the
   job of [diff coverage](diff-coverage.html).
3. **Treat covered-but-unasserted as the default suspicion.** A line
   that executes inside a test with no assertions still counts as
   covered. Coverage tells you where to look, never what to believe.
4. **Expect the last percent to lie.** Defensive branches and dead paths
   resist honest coverage, and the tests written to reach them tend to
   assert nothing.

## How it gets gamed

Line coverage is the easiest oracle in the catalog to inflate, precisely
because it measures nothing but execution:

- **Assertion-free tests.** Calling code with no assertions still
  executes it, and executed lines count. A suite can climb toward 100%
  while verifying nothing. This is the dominant gaming mode, especially
  with generated tests that import a module and call everything in it.
- **Coverage of the test, not the behavior.** Tests that assert on
  mocks and fixtures exercise their own lines, not the system's. The
  report looks healthy while the production code's behavior is never
  checked.
- **Exclusion pragmas.** `# pragma: no cover`, ignore lists, and
  rewritten conditionals quietly shrink the denominator. A rising count
  of exclusions is the metric being edited rather than earned.

The meta-signal is [mutation testing](mutation-testing.html) on the
covered code. High line coverage with a low mutation score is a suite
that executes its code without reading it.

## Response playbook

When line coverage falls or a report exposes a hole:

1. **Open the annotated source.** Locate the specific uncovered lines.
   The percentage alone tells you nothing actionable.
2. **Write one test per uncovered path, asserting on output.** Start
   with the lines that handle errors and edge inputs; they are the ones
   that fail in production. Assert on the result, not on the fact that
   the code ran.
3. **Cut dead code instead of covering it.** Lines that cannot be
   reached are not a testing gap. Deleting them raises coverage for
   free and removes the temptation to write contrived tests.
4. **Block merges that lower coverage on changed lines.** Wire a
   [diff coverage](diff-coverage.html) gate into CI so the next drop
   surfaces at review time, not in the monthly report.

## What it cannot detect

Whether the code that *executed* was actually *asserted on*. A line can
execute without any test verifying its output. This is why coverage alone
is a [weak oracle](mutation-testing.html).
