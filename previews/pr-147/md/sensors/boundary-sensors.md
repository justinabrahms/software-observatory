---
id: SO-008d
title: Boundary Sensors
family: architecture
family_num: 08
oracle: high
oracle_note: a boundary violation is definitive
independence: high
independence_note: rules are external to the code
scope: module
latency: seconds
actionability: guiding
actionability_note: names the offending file and the exact edge it crossed
type: predictive
stack_level: static-analysis
categories:
- Architecture
- Boundary Sensors
see_also:
- SO-008
- SO-008b
- SO-002
- SO-015c
last_reviewed: '2026-08-26'
references:
- title: On the Criteria To Be Used in Decomposing Systems into Modules
  year: 1972
  tier: IV
  url: https://doi.org/10.1145/361598.361623
  kind: publication
  authors: D. L. Parnas
  venue: Communications of the ACM 15(12)
- title: import-linter
  kind: tool
  url: https://import-linter.readthedocs.io
  description: Forbidden-import and layer contracts for Python
- title: Deptrac
  kind: tool
  url: https://github.com/qossmic/deptrac
  description: Layer dependency enforcement for PHP
- title: eslint-plugin-boundaries
  kind: tool
  url: https://github.com/javierbrea/eslint-plugin-boundaries
  description: Import boundary rules between element types for JavaScript/TypeScript
- title: Bazel visibility
  kind: tool
  url: https://bazel.build/concepts/visibility
  description: Build-level rules for which targets may depend on which
---

"This package must not import that package." A sensor of *encapsulation* and
module boundaries — computationally enforced, not prose rules.

Boundary sensors are the module-level version of [fitness
functions](fitness-functions.html): they assert that specific imports or
dependencies are forbidden. Unlike complexity metrics, they have high oracle
strength — a forbidden import is a definitive violation.

## In practice

A boundary sensor cashes out as a machine-checked rule in CI, typically
an import linter naming the forbidden edge:

```
contract: ui must not import from db internals
VIOLATION src/ui/dashboard.ts:14
  import { rawQuery } from "../db/internal/query";
  forbidden: src/ui/** -> src/db/internal/**
```

The reading is the violation plus the exact rule it broke, which is why
the fix is rarely ambiguous. Two habits for reading it well:

- **The rule is the design decision, not the error.** When a violation
  fires, the first question is whether the boundary or the import is
  wrong. Both answers happen. The rule exists so the team answers that
  question explicitly instead of silently merging.
- **New violations are cheap, old ones are not.** A rule that fails on
  every pre-existing violation never gets turned on. Enforce it on
  changed lines from day one and grandfather what is already there
  into an explicit allowlist with a date on it.

## How it gets gamed

A boundary is enforced by decree until the decree gets edited:

- **Grow the allowlist.** Each new violation gets an exception instead
  of a fix, and the rule passes while covering less every week. An
  allowlist that only grows is the boundary being deleted one entry at
  a time.
- **Rename the path.** Splitting `db/internal` into `db/core` so the
  new name misses the rule satisfies the linter and breaks nothing
  else. Rules that match on path strings are fragile by construction;
  rules that match on declared module edges are not.
- **Indirect through a helper.** The forbidden import moves behind a
  wrapper in an unrestricted package, and the violation becomes a
  feature. The dependency graph shows the relay; the import rule
  does not.
- **Silence the sensor.** The CI job gets marked flaky or loses its
  required status, and violations stop blocking merges without anyone
  deleting the rule.

The meta-signal is the allowlist size. Track it, and treat growth as an
event that needs a reason, not a diff that needs an approval.

## Response playbook

When a boundary violation fires:

1. **Read the rule before the code.** The violation names the exact
   edge, `ui -> db/internal`. Decide first whether the boundary is
   right; most teams skip this and go straight to suppressing the
   error.
2. **Fix the import, not the rule.** Move the needed function into a
   public module on the allowed side of the boundary. If the function
   is genuinely needed across the boundary, that is a design decision
   to make explicitly, in the rule file, with a named owner.
3. **Do not suppress to unblock.** A suppression that lands under
   deadline pressure becomes permanent. If the change cannot wait,
   move the function, not the exception.
4. **Check the diff for the indirect path.** A violation often means
   a helper now re-exports the forbidden import. Follow the import
   chain before approving.
5. **Audit the allowlist when it grows.** Every new entry needs a
   reason and an expiry. An entry without both is a boundary already
   lost.

## What it cannot detect

Boundary sensors check structural boundaries, not [behavioral
boundaries](contract-tests.html). A module can respect import boundaries
while still violating encapsulation through shared mutable state.
