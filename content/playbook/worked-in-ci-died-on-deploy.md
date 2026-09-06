---
order: 60
kind: symptom
title: "It worked in CI and died on deploy"
noticed: >-
  Every check passed. The deploy finished. The service never came up, or
  came up and returned 500 on the first real request, because of an
  environment variable, a port, or a secret that only existed on the
  laptop.
doubt: does-not-run-where-deployed
sensor: smoke-tests
next: one-slow-dependency
---

## Point this at it

[Smoke tests](smoke-tests.html), as a shell script of four curl calls
the deploy job runs against the URL it just deployed: GET /health, POST
one record, GET it back, DELETE it. Any non-2xx fails the script, and a
failed script halts the rollout or rolls it back. The run takes under a
second.

The part that matters is the target. Point it at the artifact that just
went out, in the environment it went out to. A smoke run against staging
while production stays old, or against a cached edge, is a green reading
about a system nobody is serving.

## Reading it

- Red: the deployed artifact is dead on that path in that environment.
  Re-run once to rule out bad credentials or a wrong URL; two consecutive
  failures are the artifact. Roll back, then diagnose, and keep the
  status code, body, and response time the failing check returned.
- Green: the system is alive on those four paths, here. A pass is
  necessary for the rollout to continue and sufficient for almost
  nothing else.
- It does not prove correctness on any path, behavior under load, or
  what happens when something the service depends on stops answering.

## If the doubt survives

If the smoke run is green and the service goes down later in the same
environment, it came up fine and fell over when a dependency got slow
or disappeared. That is falls over with a dependency, and the next play
is for it.
