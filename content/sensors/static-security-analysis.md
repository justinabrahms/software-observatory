---
id: SO-014
title: Static Security Analysis
family: adversarial
family_num: "05"
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

## Tooling

- Semgrep
- CodeQL
- Bandit
- brakeman

## References

- Semgrep: https://semgrep.dev
- CodeQL: https://codeql.github.com
