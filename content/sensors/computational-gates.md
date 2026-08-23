---
id: SO-011b
title: Computational Gates
family: ai-sensors
family_num: '11'
oracle: maximum
independence: maximum
scope: system
latency: seconds
actionability: guiding
type: predictive
stack_level: static-analysis
categories:
- AI-Generated
- Computational Controls
- Maximum Oracle
see_also:
- SO-011
- SO-011c
- SO-011d
last_reviewed: 2026-08-23
references:
- title: 'Gender Shades: Intersectional Accuracy Disparities in Commercial Gender
    Classification'
  year: 2018
  tier: I
  url: http://proceedings.mlr.press/v81/buolamwini18a/buolamwini18a.pdf
  kind: paper
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

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Maximum — a gate is a fact, not a suggestion |
| Independence | Maximum — the gate is external to the agent |
| Scope | System-level |
| Feedback latency | Seconds (gate execution time) |
| Actionability | Guiding — the gate tells you exactly what failed |
| Type | Predictive |

## What it cannot detect

A gate can only enforce what it's configured to check. A gate that doesn't
exist can't block anything. The gap between "should be gated" and "is gated"
is invisible.
