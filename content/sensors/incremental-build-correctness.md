---
id: SO-014d
title: Incremental Build Correctness
family: change
family_num: '07'
oracle: medium
oracle_note: divergence between declared and actual rebuild sets is meaningful but noisy
independence: high
independence_note: measures the build system, which the change author does not control
scope: system
latency: minutes
actionability: guiding
actionability_note: points at the under-declared dependency edge
type: retrospective
stack_level: static-analysis
categories:
- Change
see_also:
- SO-007b
- SO-014c
- SO-001
last_reviewed: '2026-08-24'
references:
- title: 'Reproducible Builds: Increasing the Integrity of Software Supply Chains'
  year: 2021
  tier: II
  url: https://arxiv.org/abs/2104.06020
  kind: paper
  authors: Chris Lamb, Stefano Zacchiroli
  venue: arXiv preprint; later IEEE Software 39 (2022) 62-70
- title: An Empirical Analysis of Build Failures in the Continuous Integration Workflows of Java-Based Open-Source Software
  year: 2017
  tier: II
  url: https://dsg.tuwien.ac.at/team/trausch/pub/PID4727015.pdf
  kind: paper
  authors: Thomas Rausch, Waldemar Hummer, Philipp Leitner, Stefan Schulte
  venue: MSR 2017
- title: Bazel
  url: https://bazel.build
  kind: tool
  description: Google's build system
- title: Buck
  kind: tool
  url: https://buck.build
  description: Meta's build system
- title: Nix
  kind: tool
  url: https://nixos.org
  description: Reproducible build system and package manager
- title: ccache
  kind: tool
  url: https://ccache.dev
  description: Compiler cache for fast rebuilds
scope_note: the whole codebase's build graph
---

Did the build system actually rebuild everything this change touched?
Incremental builds and remote caches save hours, and silently shipping a
stale artifact is the price when the dependency graph they trust is wrong.
This sensor compares what the change *should* have invalidated against what
the build *did* invalidate.

## In practice

The reading is a set difference between two lists: every target the
change should have invalidated, and every target the build actually
rebuilt. When they match, the incremental graph is telling the truth.

```
change:    edit src/render/theme.css
expected:  [pages/home.html, pages/about.html, pages/docs.html]
rebuilt:   [pages/home.html]
missing:   [pages/about.html, pages/docs.html]
verdict:   STALE: 2 targets shipped without rebuild
```

The verdict only exists because of the counterfactual: the same
change through a clean build. That is the reference the sensor is
compared against, so "clean rebuild on CI matched, incremental on a
developer machine did not" is itself a finding, not a coincidence.

The reading habit that matters: when a behavior change ships without a
rebuild record, check the graph before checking the code. Stale
artifacts masquerade as caching bugs, flaky behavior, and "works on
my machine," and the distinguishing fact is always whether the target
that changed state was in the rebuilt set.

## Response playbook

When the rebuild set comes up short:

1. **Reproduce with a clean build.** If the clean build fixes the
   symptom, staleness is confirmed and the graph is the culprit.
2. **Find the undeclared edge.** Walk from the edited file to the
   stale target; the missing declaration is usually a generated
   file, a header, or a config read at runtime but not at build
   time.
3. **Declare the dependency; do not script around it.** A clean
   build on every CI run papers over the hole and burns the hours
   the cache was built to save.
4. **Add the stale target to the regression set** so the next
   undeclared edge fails the same check instead of shipping.

## How it gets gamed

- **Manual cache busting.** Touching files or bumping fake hashes to
  force a rebuild, instead of fixing the dependency declaration. The
  graph stays wrong; the workaround becomes load-bearing.
- **Clean builds by decree.** "Just run clean" as the sanctioned fix
  converts a correctness bug into a permanent performance tax and
  hides the sensor entirely.
- **Undeclared inputs rationalized.** Files read at build time that
  the manifest never lists, because declaring them was "too
  invasive." Every one is a future stale artifact.

The meta-signal is cache-hit correctness: sampled rebuilds whose
outputs differ from the cached artifact they replaced.

## What it cannot detect

Changes whose *semantic* effect exceeds their declared dependencies in ways
no graph captures (a shared constant edited in a header the graph treats as
irrelevant). That class of surprise is what
[API compatibility](api-compatibility.html) and
[integration tests](integration-tests.html) exist for.
