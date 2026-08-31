---
id: SO-014
title: Static Security Analysis
family: adversarial
family_num: '05'
oracle: medium
oracle_note: findings need triage; false positives are the tax
independence: high
independence_note: the analysis does not trust the code's own intentions
scope: system
latency: minutes
actionability: blocking
type: predictive
stack_level: static-analysis
categories:
- Adversarial
see_also:
- SO-005
- SO-005c
- SO-001c
- SO-014b
last_reviewed: '2026-08-31'
references:
- title: An Empirical Study on the Effectiveness of Security Code Review
  year: 2013
  tier: I
  url: https://people.eecs.berkeley.edu/~daw/papers/coderev-essos13.pdf
  kind: publication
  authors: Anne Edmundson, Brian Holtkamp, Emanuel Rivera, Matthew Finifter, Adrian Mettler, David Wagner
  venue: ESSoS 2013
- title: Eliminating Memory Safety Vulnerabilities at the Source
  year: 2024
  tier: II
  url: https://security.googleblog.com/2024/09/eliminating-memory-safety-vulnerabilities-Android.html
  kind: publication
  authors: Google Security Blog, Android team
  venue: Google Security Blog
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
  url: https://bandit.readthedocs.io
  description: Python security linter
- title: brakeman
  kind: tool
  url: https://brakemanscanner.org
  description: Static security analysis for Rails
scope_note: the whole codebase
---

Attacking the code before it runs. Taint tracking, dataflow analysis, and
pattern-based scanners (Semgrep, CodeQL) ask: "is there any path through
this program where an adversary's input reaches a dangerous sink?" A sensor
of exploitable structure, not of known-bad strings.

## In practice

A scanner reading is a source-to-sink path with a severity attached,
not a bare pattern match:

```
semgrep --config p/owasp-top-ten src/
src/api/search.py:31: Possible SQL injection (high)
  query = "SELECT * FROM items WHERE name = '%s'" % request.args["q"]
  taint: request.args["q"] -> cursor.execute(query)
```

The value is the path. The finding is not "this string looks
dangerous" but "input from here reaches that sink through these
lines," and the reading takes minutes because the intermediate steps
are printed.

Severity is the scanner's estimate, not the exploitability. A high
finding behind an authenticated, sanitized code path may matter less
than a medium one on an anonymous endpoint, and the scanner knows
neither the auth model nor the traffic. Which is why triage reads the
path first and the badge second, and why the same finding can be a
blocker in one service and a note in another.

## Response playbook

When the scanner fires:

1. **Trace the full path before judging severity.** The scanner shows
   the chain; confirm whether anything in between already
   sanitizes, authenticates, or bounds the input.
2. **If reachable, fix at the sink.** Parameterized queries,
   escaping APIs, allowlists. Point fixes outlive pattern fixes.
3. **If unreachable, record why.** A one-line justification at the
   finding site keeps the next reviewer from redoing the triage.
4. **Fix the class, then add the rule.** If the sink exists in ten
   other places, the scanner's job is to find all ten; wire that
   rule into CI as blocking before the next one ships.
5. **Treat untriaged findings as broken builds.** A backlog of
   undated security findings is a queue that never drains.

## How it gets gamed

- **Severity downgrade by triage.** Marking a finding "won't fix"
  with a one-word justification is the cheapest override available
  to a reviewer. The meta-signal is the ratio of suppressed to
  confirmed findings, and the age of the suppressed ones.
- **Baseline erosion.** Freezing the finding count in a baseline
  file and only failing on new ones, while the baseline quietly
  grows forever because "old findings are someone else's problem."
- **Rule-set narrowing.** Disabling taint rules because they are
  noisy and keeping only the pattern matches, which detect the
  least of the three.
- **Scanner shopping.** Running the tool that finds the fewest
  issues in review and calling it "our SAST."

## What it cannot detect

Vulnerabilities in the composition of services, in configuration, or in the
dependencies' runtime behavior — those belong to
[fault injection](fault-injection.html) and [live
chaos](live-chaos-experiments.html). And a clean scan says nothing about
attacks that arrive through valid inputs: [fuzzing](fuzzing.html) covers
that side.

Security is a deeper topic than this catalog covers. SAST is one sensor in
the adversarial family — it asks whether an adversary's input can reach a
dangerous sink — but the broader practice of application security
(threat modeling, penetration testing, dependency vulnerabilities, runtime
exploit detection) deserves its own resources. See
[OWASP](https://owasp.org) and the
[CWE](https://cwe.mitre.org) for dedicated treatment.
