---
id: SO-002b
title: Example-Based Tests
family: behavioral
family_num: '02'
oracle: high
oracle_note: assertion failure is definitive
independence: low
independence_note: same author writes code and tests
scope: function
latency: seconds
actionability: guiding
actionability_note: shows expected vs actual
type: predictive
stack_level: behavioral-tests
categories:
- Behavioral
see_also:
- SO-002c
- SO-002d
- SO-003
last_reviewed: '2026-08-24'
references:
- title: Techniques for Improving Regression Testing in Continuous Integration Development Environments
  year: 2014
  tier: I
  url: https://cs.uwaterloo.ca/~m2nagapp/courses/CS846/1171/papers/elbaum_fse14.pdf
  kind: paper
  authors: Sebastian Elbaum, Gregg Rothermel, John Penix
  venue: FSE 2014 (ESEC/FSE), Hong Kong
- title: On the Effectiveness of the Test-First Approach to Programming
  year: 2005
  tier: I
  url: https://www.cs.unm.edu/~joel/cs351/paper/IEEE-Effectiveness_of_Test-First_Approach_to_Programming.pdf
  kind: paper
  authors: Hakan Erdogmus, Maurizio Morisio, Marco Torchiano
  venue: IEEE TSE 31(1)
- authors: Beizer
  title: Software Testing Techniques
  year: 1990
  kind: paper
  tier: IV
- title: pytest
  kind: tool
  url: https://docs.pytest.org
  description: Python testing framework
- title: Jest
  kind: tool
  url: https://jestjs.io
  description: JavaScript testing framework
- title: JUnit
  kind: tool
  url: https://junit.org
  description: Java testing framework
- title: Go testing
  kind: tool
  url: https://pkg.go.dev/testing
  description: Go's built-in testing package
---

Given X, expect Y. The fundamental behavioral sensor.

Fundamentally different from [coverage](diff-coverage.html): coverage says
"this code executed." A behavioral assertion says "this code produced the
*right result*." That is a massive distinction.

## The weakness

Example-based tests are only as good as the examples chosen. They test what
the author thought to test. [Mutation testing](mutation-testing.html) and
[metamorphic testing](metamorphic-testing.html) exist to find the gaps.

## In practice

A reading is an assertion failure with both sides of the comparison
spelled out:

```
FAILED tests/test_pricing.py::test_discount_applies_above_threshold

tests/test_pricing.py:42: in test_discount_applies_above_threshold
    assert price_with_discount(100, tier="gold") == 90.0
E   AssertionError: assert 95.0 == 90.0
E    +  where 95.0 = price_with_discount(100, tier='gold')

================== 1 failed, 213 passed in 4.21s ==================
```

Reading it well takes three habits:

1. **Read the assertion before the code.** The failure shows two
   values; the first question is which one is wrong. The assertion
   encodes the intended behavior, and sometimes it is the test that
   needs fixing, not the code.
2. **One failure is a signal, not a ratio.** "1 failed, 213 passed"
   is not 99.5% healthy. The pass count is context; the failure is
   the reading.
3. **Separate the verdict from the harness.** An assertion error is a
   behavioral reading. A collection error, import error, or fixture
   timeout is the harness breaking, which means the suite produced no
   reading at all.

## How it gets gamed

The suite belongs to the same people as the code, so it can be bent:

- **Delete or skip the failure.** `skip`, `xfail`, and "I will fix
  it tomorrow" turn red to green without touching the code. A rising
  skip count is the suite telling you it is being silenced.
- **Weaken the assertion.** Replacing `== 90.0` with `is not None`
  makes the test pass and the sensor blind. The test still runs, so
  the suite looks healthy while detecting less.
- **Pin the symptom.** Hard-coding the current output into the
  expectation turns the test into a tautology that passes for any
  implementation.
- **Sample only the happy path.** Choosing examples that avoid the
  buggy branch keeps the suite green and the bug alive. [Mutation
  testing](mutation-testing.html) is the sensor for this gap.

The meta-signal is the skip count plus the share of test-file diffs
that weaken an assertion. Neither shows up in coverage.

## Response playbook

When a test fails:

1. **Reproduce it locally.** A failure you cannot reproduce is not
   yet a finding; it is a question. Get the exact input and the
   exact assertion before anything else.
2. **Decide which side is wrong.** The assertion encodes intended
   behavior. If the code violated it, fix the code. If the
   expectation was wrong, fix the test and say why, because a
   silently rewritten expectation is a deleted sensor.
3. **Fix the cause, then re-run the full suite.** A fix that breaks
   a sibling test has revealed a second assumption you did not know
   you had.
4. **Add the neighbor cases.** If `100` failed, the values just
   above and below the boundary are now suspects. The failure is a
   free tour of the edge of the behavior.
5. **Never delete the test to unblock a merge.** If the test is
   wrong, rewrite it with the reason in the commit. If it is right,
   the merge is not done.

## What it cannot detect

Missing behavior, untested edge cases, and [integration
failures](contract-tests.html) that emerge only when components are
connected.
