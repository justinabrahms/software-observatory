---
id: SO-011b
title: Computational Gates
family: ai-sensors
family_num: '11'
oracle: maximum
oracle_note: a gate is a fact, not a suggestion
independence: maximum
independence_note: the gate is external to the agent
scope: system
latency: seconds
latency_note: gate execution time
actionability: guiding
actionability_note: the gate tells you exactly what failed
type: predictive
stack_level: static-analysis
categories:
- AI-Generated
- Maximum Oracle
see_also:
- SO-011
- SO-011c
- SO-011d
last_reviewed: '2026-08-24'
references:
- title: 'Gender Shades: Intersectional Accuracy Disparities in Commercial Gender Classification'
  year: 2018
  tier: I
  url: http://proceedings.mlr.press/v81/buolamwini18a/buolamwini18a.pdf
  kind: paper
  authors: Joy Buolamwini, Timnit Gebru
  venue: PMLR 81 / FAT* 2018
- title: GitHub Actions
  kind: tool
  url: https://docs.github.com/actions
  description: CI/CD workflow automation
- title: GitLab CI
  kind: tool
  url: https://docs.gitlab.com/ee/ci/
  description: GitLab's built-in CI/CD
- title: Jenkins
  kind: tool
  url: https://www.jenkins.io
  description: Extensible automation server
- title: pre-commit hooks
  kind: tool
  url: https://pre-commit.com
  description: Pre-commit framework for git hooks
---

An instruction saying "verify this" is weaker than a gate that literally
refuses to proceed unless the verification command succeeded. *Controls,
not rules.*

Computational gates are the enforcement mechanism: not "please run the
tests" but a CI pipeline that blocks merge if tests fail. Not "please check
types" but a build step that fails on type errors. The distinction between
prose rules and computational gates is critical for [agentic
coding](catalog.html#ai-sensors) — agents will skip prose rules if they
can.

## What a gate looks like

```yaml
# GitHub Actions: a required status check
- name: Run tests
  run: make test
# If this fails, the PR cannot merge — the gate refuses to proceed.
```

A hard gate refuses to proceed: a required CI check that blocks merge, a
pre-deploy hook that aborts on failure. A soft gate warns but allows
override: a non-required check, a Slack notification. The distinction
matters — soft gates are suggestions with ceremony; hard gates are
controls.

## The override problem

Every gate has a bypass path. "I know, I know, just ship it." The gate's
real strength is measured by how hard the bypass is: a one-click override
is a soft gate regardless of what the config says. A gate that requires
two-person approval, an audited ticket, and a 24-hour cooldown is a real
gate. Computational gates fail when the bypass is itself computational and
auditable — every override should leave a trail.

## In practice

A gate reading is the check list on a change: one line per gate, each
with a verdict. In a GitHub-style pull request:

```
✗ test        make test             4m   Process completed with exit code 1.
✓ types       make typecheck        1m
✓ coverage    diff-cover >= 80%     2m
✗ arch        fitness functions     3m   1 violation

Merging is blocked: 2 required checks failed
```

The output of the failing step is the actual reading:

```
FAILED tests/test_billing.py::test_refund
make: *** [Makefile:12: test] Error 1
```

Reading it well:

1. **The verdict is binary; the output is the content.** "Merging is
   blocked" is the sensor firing. The failing command's output names
   exactly what to fix, which is what makes gates cheap to act on.
2. **Check that the gate is required.** A failing check that does not
   block merge is a soft gate, whatever its name implies. The merge box
   is the ground truth, not the workflow file.
3. **A green gate is a statement about what is checked.** Green means
   the configured commands passed, nothing more. Gates that do not run
   on the change, or run against a stale base, read green while
   verifying little.
4. **Time is part of the reading.** A gate that takes 40 minutes changes
   behavior: people batch work around it or override it. Slow gates
   erode their own authority.

## How it gets gamed

The override problem above covers bypassing a gate. The subtler failure
modes edit the gate itself:

- **Tautological gates.** A step that always exits zero defeats the
  gate without touching its status: `make test || true`, a test command
  pointed at the wrong directory, an empty test suite reporting
  success. The check stays required and green while checking nothing.
- **Gate editing as part of the change.** A diff that both breaks a
  rule and removes the check that enforces it gets reviewed as two
  innocent halves. Gate definitions need to be harder to change than
  the code they gate: separate review, restricted ownership.
- **Retry-to-green.** If the gate is flaky, "re-run until it passes"
  becomes the de facto bypass. Each retry discards one real failure
  reading. Track how often failing runs are retried rather than read.
- **Routing around the gate.** Landing changes on a branch, repo, or
  hotfix path without the required checks. The gate is real everywhere
  except where it matters.

The meta-signal is the gate definition history. When the workflow file
changes more often than it catches failures, the gate is being
negotiated with.

## Response playbook

When a gate fails, or is suspected of being weaker than it claims:

1. **Read the failing step's output and fix the code.** The gate names
   the exact command and error. Fix the underlying failure; do not
   re-run hoping for a different result.
2. **Never make the gate tautological to unblock.** No `|| true`, no
   empty suite, no scope narrowed to exclude the failure. If the gate
   itself is wrong, change it in a separate, explicitly reviewed
   commit.
3. **If a retry turns it green, treat the first run as the finding.**
   Log the flaky gate and fix it. A flake retried into silence is a
   bypass without an override button.
4. **Audit the bypass cost quarterly.** List every gate and how hard it
   is to skip: who can override, what trail it leaves, what cooldown
   applies. One-click overrides are soft gates, whatever the config
   says.
5. **Verify the gate is required where it counts.** Check branch
   protection and merge rules on the branches that actually ship. A
   required check that a human can mark successful anyway is not a
   gate.

## What it cannot detect

A gate can only enforce what it's configured to check. A gate that doesn't
exist can't block anything. The gap between "should be gated" and "is gated"
is invisible.
