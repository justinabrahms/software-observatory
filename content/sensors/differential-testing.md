---
id: SO-005c
title: Differential Testing
family: adversarial
family_num: '05'
oracle: high
oracle_note: disagreement is definitive evidence of a bug
independence: high
independence_note: two independent implementations
scope: function
latency: minutes-hours
actionability: guiding
actionability_note: shows the divergent inputs and outputs
type: predictive
stack_level: property-metamorphic
categories:
- Adversarial
- Oracle-Free
see_also:
- SO-005
- SO-005b
- SO-005d
last_reviewed: '2026-08-24'
references:
- title: 'Elle: Inferring Isolation Anomalies from Experimental Observations'
  year: 2020
  tier: II
  url: https://arxiv.org/abs/2003.10554
  kind: paper
  authors: Kyle Kingsbury, Peter Alvaro
  venue: arXiv 2003.10554
- title: Yang et al., 'Finding and Understanding Bugs in C Compilers' (2011, Csmith)
  kind: other
- title: SQLancer
  url: https://github.com/sqlancer/sqlancer
  kind: tool
  description: Differential testing for SQL databases
- title: Csmith
  kind: tool
  url: https://embed.cs.utah.edu/csmith
  description: Random C program generator for compiler testing
---

`implementation_A(input) == implementation_B(input)`. You don't know which is
right. But disagreement is an excellent sensor.

## The oracle question

Differential testing is oracle-free: you don't need to know the correct
answer, only whether two implementations agree. This makes it powerful for
systems where computing the expected output is infeasible.

```
old implementation vs new implementation
production implementation vs reference implementation
database query vs independently computed result
two parsers
two serialization formats
compiler vs interpreter
```

## Where it shines

Differential testing earned its reputation in domains where multiple
independent implementations of the same spec exist:

- **Compiler fuzzing**: Csmith generates random C programs, feeds them to
  GCC, Clang, and MSVC, and flags disagreements. This found hundreds of
  compiler bugs.
- **Spec conformance**: TLS, JSON, and XML parser differential testing —
  feed the same inputs to multiple parsers, flag disagreements. The JSON
  parser differential testing work found conformance bugs in every major
  parser.
- **Database engines**: running the same SQL against Postgres, MySQL, and
  SQLite and comparing results.

In each case, you don't need to know the correct answer — you only need
two implementations that *should* agree.

## In practice

A reading is two outputs for one input, with the disagreement
flagged:

| Input | Engine A (Postgres) | Engine B (SQLite) | Verdict |
|-------|---------------------|-------------------|---------|
| `SELECT 3 + 4` | 7 | 7 | agree |
| `SELECT 1 / 0` | ERROR: division by zero | NULL | disagree |
| `SELECT 'abc' + 1` | ERROR | 1 | disagree |

The tooling writes each divergent case to disk as the report:

```
[mismatch] seed 0x8f3a2c
  query:     SELECT 1 / 0
  engine A:  ERROR: division by zero
  engine B:  NULL
  reduced input saved to findings/0x8f3a2c.sql
```

Reading it well:

1. **Disagreement means at least one is wrong, not both.** The
   reading is a fact about the pair; assigning blame is a separate
   step against the spec.
2. **Check whether the spec is silent.** Some disagreements live in
   undefined territory where each engine picked its own answer. Those
   are spec bugs as much as implementation bugs, and they will bite
   anyone who assumed otherwise.
3. **Trust the reduced input, not the original.** Generated cases
   are enormous; the minimized case is the one a human can verify by
   hand, and the one worth filing.

## How it gets gamed

The sensor is a comparison, and comparisons can be rigged:

- **Cherry-pick the reference.** The reference implementation is
  chosen for convenience, not correctness. When it is the weaker
  half of the pair, disagreements get resolved in its favor by
  default, which silently converts "does my code match the spec"
  into "does my code match the thing I picked." The fix is to judge
  divergences against the spec, never against the reference.
- **Filter the input distribution.** Narrow the generator, or prune
  the seed corpus after a big finding, until the divergent region
  stops being sampled. The campaign still runs and the report stays
  clean, because the inputs that would have caught the bug are no
  longer in the lottery.
- **Label divergences as flaky.** Real nondeterminism exists, but a
  disagreement that comes and goes is usually an ordering or
  precision bug on one side, not noise. Retrying until the two
  agree launders the finding.
- **Exempt input classes.** "Undefined behavior," "unsupported
  locale," "legacy format": every excluded class is a place where
  disagreement is ruled out by decree. Some exclusions are
  legitimate; an exclusion list that grows right after findings is
  a gaming pattern.

The meta-signal is the exclusion list plus the disagreement-dismissal
rate. Findings should be closed by the spec, not by policy.

## Response playbook

When two implementations disagree:

1. **Preserve the divergent input.** The reduced case is the
   reading; commit it before it is lost to the next campaign.
2. **Judge against the spec, not the majority.** Disagreement means
   at least one implementation is wrong; the spec says which. If the
   spec is silent, both answers are defensible and the spec is the
   bug.
3. **Fix the implementation you own.** If one side is yours, the
   other implementation's output, judged against the spec, is a test
   case written for free.
4. **Add the case to the suite.** A divergence found once is worth
   pinning forever, because the fix can regress without anyone
   re-running the campaign.

## What it cannot detect

If both implementations share the same bug, differential testing won't find
it. Also requires two implementations, which may not exist.
