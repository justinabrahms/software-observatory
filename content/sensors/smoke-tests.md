---
id: SO-012b
title: Smoke Tests
family: behavioral
family_num: '02'
oracle: medium
oracle_note: '"alive" is a weak claim, but a true one'
independence: high
independence_note: exercises the real deployed artifact end to end
scope: user-journey
latency: seconds
actionability: blocking
actionability_note: a failed smoke test halts the rollout
type: retrospective
stack_level: canary-shadow
categories:
- Behavioral
- Deployment Safety
see_also:
- SO-002c
- SO-007
- SO-013b
last_reviewed: '2026-08-24'
references:
- title: 'Software Engineering at Google, ch. 11: Testing Overview'
  year: 2020
  tier: IV
  url: https://abseil.io/resources/swe-book/html/ch11.html
  kind: publication
  authors: Adam Bender; eds. Titus Winters, Tom Manshreck, Hyrum Wright
  venue: O'Reilly Media
- title: curl-based smoke tests
  kind: tool
  url: https://curl.se
  description: Basic HTTP endpoint checks via curl
- title: k6 smoke
  kind: tool
  url: https://k6.io
  description: Smoke testing with k6 load testing tool
scope_note: critical user paths through the deployed system
---

The cheapest behavioral check against a live deployment: hit `/health`,
create one record, read it back, delete it. If any step fails, roll back.
Smoke tests answer "is the deployed system alive enough to behave at all?"
before [canary analysis](canary-analysis.html) has enough traffic to judge.

## In practice

A reading is a short checklist run against the freshly deployed
artifact, one line per vital sign:

```
$ smoke https://staging.example.com
  GET    /health            200   41ms  ok
  POST   /records           201   87ms  ok
  GET    /records/8f3a      200   33ms  ok
  DELETE /records/8f3a      204   52ms  ok
4/4 passed in 0.9s
```

The same run, failing:

```
  GET    /health            200   39ms  ok
  POST   /records           500  102ms  FAIL
  GET    /records/8f3a      404   28ms  FAIL (depends on POST)
  DELETE /records/8f3a      skipped
1/4 passed. ROLLBACK.
```

Reading it well:

1. **A failed smoke test is a blocking verdict, not a triage item.**
   The whole point of the sensor is that it runs before real traffic
   arrives. Debating the failure while the rollout continues defeats
   it.
2. **Rule out the harness once, then trust the reading.** Bad
   credentials or a wrong URL produce the same red line as a broken
   deployment. Re-run once; two consecutive failures are the
   artifact.
3. **Do not read more into a pass than it contains.** Four green
   lines mean the system is alive on four paths. They say nothing
   about scale, correctness, or the other paths.

## How it gets gamed

- **Shrink the checklist.** Removing the failing endpoint from the
  smoke set turns the sensor into a decoration. The smoke test now
  passes and says less.
- **Point at the wrong target.** A smoke run against staging while
  production stays old, or against a cached edge, produces green
  readings about a system nobody is serving.
- **Loosen the verdict.** Turning a failed check into a warning
  keeps the run and discards the gate. The rollout proceeds on the
  same evidence, minus the evidence.

The meta-signal is the check count over time. A smoke suite that
shrinks after failures is being gamed.

## Response playbook

When a smoke test fails:

1. **Stop the rollout.** The sensor exists to run before real
   traffic arrives; debating the failure while the deploy continues
   defeats the point of it.
2. **Rule out the harness once.** Bad credentials, a wrong URL, and
   a downed test runner produce the same red line as a broken
   artifact. Re-run once; two consecutive failures are the artifact.
3. **Roll back, then diagnose.** Restore the known-good version
   before investigating. The smoke test is a blocking verdict by
   design; the post-mortem is for after, not instead.
4. **Capture what the failing check returned.** The status code,
   the body, and the response time are the reading. Without them,
   the post-mortem reconstructs from memory.

## What it cannot detect

Anything that requires real load, real data shapes, or real user behavior.
A smoke test passing is necessary for the deployment to proceed and
sufficient for almost nothing else.
