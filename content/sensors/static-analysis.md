---
id: SO-001e
title: Static Analysis
family: structural
family_num: '01'
oracle: medium
oracle_note: findings are patterns, not proofs
independence: high
independence_note: the analysis does not trust the code's own intentions
scope: module
scope_note: typically module to system
latency: seconds
actionability: guiding
actionability_note: shows the rule, the line, and often the fix
type: predictive
stack_level: static-analysis
categories:
- Structural
see_also:
- SO-001
- SO-001c
- SO-001d
- SO-014
last_reviewed: '2026-08-28'
references:
- title: 'How Many of All Bugs Do We Find? A Study of Static Bug Detectors'
  year: 2018
  tier: I
  url: https://software-lab.org/publications/ase2018_static_bug_detectors_study.pdf
  kind: publication
  authors: Andrew Habib, Michael Pradel
  venue: ASE 2018
- title: Lessons from Building Static Analysis Tools at Google
  year: 2018
  tier: III
  url: https://research.google/pubs/lessons-from-building-static-analysis-tools-at-google/
  kind: publication
  authors: Caitlin Sadowski, Edward Aftandilian, Alex Eagle, Liam Miller-Cushon, Ciera Jaspan
  venue: Communications of the ACM 61(4)
- title: Infer
  url: https://fbinfer.com
  kind: tool
  description: Separation logic and taint analysis by Meta
- title: CodeQL
  url: https://codeql.github.com
  kind: tool
  description: Semantic code analysis engine by GitHub
- title: Semgrep
  url: https://semgrep.dev
  kind: tool
  description: Multi-language static analysis with custom rules
- title: Clang Static Analyzer
  url: https://clang-analyzer.llvm.org
  kind: tool
  description: Path-sensitive analysis for C/C++/Objective-C
- title: Pylint
  url: https://pylint.readthedocs.io
  kind: tool
  description: Python static analysis and style checker
---

Pattern-matching and dataflow analysis over the source without executing it.
Covers the space between a [linter](linter.html) (style and local patterns)
and a [type checker](type-checker.html) (type soundness): null dereferences,
unreachable code, resource leaks, taint flow, API misuse. It subsumes
neither neighbor: it carries no style rules and proves no types. It also
gets adopted differently. A linter arrives with the toolchain and runs from
the first commit; a dataflow analyzer is slower, noisier out of the box, and
has to be tuned against the codebase before its output is worth reading, so
teams switch it on deliberately and usually later. What it buys for that
cost is reasoning that follows values across function boundaries and down
particular execution paths, which neither neighbor attempts.

## In practice

A reading is a finding with a rule, a location, and usually a trace:

```
infer run -- javac ./src
src/Checkout.java:42: error: NULL_DEREFERENCE
  object `user` last assigned on line 38 could be null
  -> called from placeOrder(src/Checkout.java:24)
  -> where `user` is the return of findById(session, id)
```

The trace is the value. A linter points at a line; a static analyzer
reconstructs how a value got there, which is what makes the finding
actionable rather than just located.

## How it gets gamed

- **Disable, don't fix.** Like the linter, `// nolint` and rule
  exclusions turn findings into noise by decree. The suppression ratio
  is the meta-signal.
- **Narrow the analysis scope.** Excluding generated directories,
  vendored code, or "legacy" modules shrinks what the analyzer sees
  while keeping its name on the pipeline.
- **Tune for silence.** Lowering sensitivity thresholds until the
  finding count drops to zero keeps the sensor and discards its reach.
- **Baseline erosion.** Freezing known findings into a baseline and
  only failing on new ones, while the baseline grows forever because
  old findings are "someone else's problem."

The meta-signal is the trend of the unsuppressed finding count per
commit. A rising baseline or a falling suppression ratio both indicate
the sensor being neutered.

## What it cannot detect

Static analysis cannot detect [behavioral correctness](catalog.html#behavioral) —
it reasons about the code, not its execution. It will not catch a wrong
algorithm that type-checks and follows every pattern rule. It also
produces false positives on code paths the analyzer's abstraction can't
prove safe, which is the cost of path-sensitivity: precision trades
against noise. A clean scan says nothing about what the code does at
runtime — that belongs to [observability events](observability-events.html)
and [runtime invariants](runtime-invariants.html).
