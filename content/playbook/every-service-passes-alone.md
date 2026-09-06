---
order: 50
kind: symptom
title: "Every service passes alone, the system fails together"
noticed: >-
  Each service's suite is green. Wire two of them together and a request
  dies at the boundary: a field serialized one way and parsed another, a
  timeout one side never expected, a status code the caller does not
  handle.
doubt: emergent-failure
sensor: integration-tests
next: worked-in-ci-died-on-deploy
---

## Point this at it

[Integration tests](integration-tests.html), one of them, across the
boundary the last failure crossed, with the real thing on the far side.
Bring the dependency up with Testcontainers or Docker Compose, then make
one round trip through it: write a record and read it back, or call the
downstream service and parse the response it actually sends. Do not stub
the side that failed. If the failure was at the user-facing edge, the
same test in Playwright against a running stack is the same sensor one
layer up.

## Reading it

- Red: a failure at the wire. Ask which side. "Role does not exist" is
  the harness and tells you nothing about your code. "502 where JSON was
  promised" is the boundary. Fix the boundary, and do not raise the
  timeout to make it pass.
- Green: these two versions talk correctly on this path. One failure in
  ten runs is a finding about a timing assumption, so treat it as a
  reading rather than a retry.
- It does not prove anything about a dependency you stubbed; that test
  checks your assumptions about the real thing. And passing against a
  local container says nothing about the environment you deploy to.

## If the doubt survives

If the pieces talk correctly in the harness and the system still fails
once deployed, the wiring is fine and the environment is not: a config
value missing, a port wrong, a service that never comes up. That is does
not run where deployed, and the next play covers it.
