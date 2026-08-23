---
id: SO-014
title: Static Security Analysis
family: adversarial
family_num: '05'
oracle: medium
independence: high
scope: codebase
latency: minutes
actionability: blocking
type: predictive
stack_level: static-analysis
categories:
- Adversarial
- Security
see_also:
- SO-005
- SO-005c
- SO-001c
last_reviewed: 2026-08-23
references:
- title: An Empirical Study on the Effectiveness of Security Code Review
  year: 2013
  tier: I
  url: https://people.eecs.berkeley.edu/~daw/papers/coderev-essos13.pdf
  kind: paper
- title: Eliminating Memory Safety Vulnerabilities at the Source
  year: 2024
  tier: II
  url: https://security.googleblog.com/2024/09/eliminating-memory-safety-vulnerabilities-Android.html
  kind: paper
- title: Semgrep
  url: https://semgrep.dev
  kind: tool
  description: Multi-language static analysis with custom rules
- title: CodeQL
  url: https://codeql.github.com
  kind: tool
  description: Semantic code analysis engine by GitHub
- title: Bandit
  kind: tool
  url: ''
  description: Python security linter
- title: brakeman
  kind: tool
  url: ''
  description: Static security analysis for Rails
---

Attacking the code before it runs. Taint tracking, dataflow analysis, and
pattern-based scanners (Semgrep, CodeQL) ask: "is there any path through
this program where an adversary's input reaches a dangerous sink?" A sensor
of exploitable structure, not of known-bad strings.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | Medium — findings need triage; false positives are the tax |
| Independence | High — the analysis does not trust the code's own intentions |
| Scope | Codebase |
| Feedback latency | Minutes |
| Actionability | Blocking when wired into CI |
| Type | Predictive |

## What it cannot detect

Vulnerabilities in the composition of services, in configuration, or in the
dependencies' runtime behavior — those belong to
[fault injection](fault-injection.html) and live chaos. And a clean scan
says nothing about attacks that arrive through valid inputs:
[fuzzing](fuzzing.html) covers that side.

Security is a deeper topic than this catalog covers. SAST is one sensor in
the adversarial family — it asks whether an adversary's input can reach a
dangerous sink — but the broader practice of application security
(threat modeling, penetration testing, dependency vulnerabilities, runtime
exploit detection) deserves its own resources. See
[OWASP](https://owasp.org) and the
[CWE](https://cwe.mitre.org) for dedicated treatment.
