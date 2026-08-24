---
id: SO-002c
title: Integration Tests
family: behavioral
family_num: '02'
oracle: high
oracle_note: failure means the integration is broken
independence: low
independence_note: same team writes code and tests
scope: service
latency: minutes
actionability: guiding
actionability_note: shows which integration point failed
type: predictive
stack_level: integration-tests
categories:
- Behavioral
see_also:
- SO-002
- SO-002b
- SO-002d
last_reviewed: '2026-08-24'
references:
- title: Techniques for Improving Regression Testing in Continuous Integration Development Environments
  year: 2014
  tier: I
  url: https://cs.uwaterloo.ca/~m2nagapp/courses/CS846/1171/papers/elbaum_fse14.pdf
  kind: paper
  authors: Sebastian Elbaum, Gregg Rothermel, John Penix
  venue: FSE 2014 (ESEC/FSE), Hong Kong
- title: Taming Google-Scale Continuous Testing
  year: 2017
  tier: II
  url: https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/45861.pdf
  kind: paper
  authors: Atif Memon, Zebao Gao, Bao Nguyen, Sanjeev Dhanda, Eric Nickell, Rob Siemborski, John Micco
  venue: ICSE 2017, Software Engineering in Practice (SEIP)
- title: pytest
  kind: tool
  url: https://docs.pytest.org
  description: Python testing framework
- title: JUnit
  kind: tool
  url: https://junit.org
  description: Java testing framework
- title: Testcontainers
  kind: tool
  url: https://www.testcontainers.org
  description: Integration testing with Docker containers
- title: Docker Compose
  kind: tool
  url: https://docs.docker.com/compose
  description: Multi-container orchestration for testing
---

Does the thing work when connected to its actual dependencies? Catches
failures that [unit tests](example-based-tests.html) structurally cannot
see — connection failures, serialization mismatches, timeout behavior.

## In practice

A reading is a failure at the boundary between the code and something
it depends on, in a suite whose unit tests stayed green:

```
FAILED tests/test_orders_repo.py::test_order_round_trip
sqlalchemy.exc.OperationalError:
  connection to server at "localhost" (127.0.0.1), port 5432 failed:
  FATAL:  role "orders_test" does not exist

FAILED tests/test_invoice_api.py::test_create_invoice
requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1
  server returned: b'<html>502 Bad Gateway</html>'
```

Three habits matter when reading these:

1. **Ask which side of the wire failed.** A unit-level assertion
   failure says the logic is wrong. An integration failure says the
   connection is wrong: the service, the schema, the serialization,
   or the network. The stack trace usually names the side.
2. **Split environment failures from boundary failures.** "Role does
   not exist" is the harness. "502 where JSON was promised" is a real
   mismatch between what the code sends and what the dependency
   accepts. Both are red; only one is about your code.
3. **Treat a single flake as a finding.** An integration test that
   fails one run in ten encodes a timing or ordering assumption that
   holds most of the time. That is the sensor working, faintly.

## How it gets gamed

Integration tests are slow and flaky enough that people have reasons:

- **Mock away the integration.** Replacing the real dependency with
  a stub turns a test of the boundary into a test of the stub's good
  manners. The test passes and the boundary remains untested.
- **Mark flakes as expected.** Retries, allowed-failure lists, and
  quarantine convert intermittent red into permanent green without
  fixing the timing assumption underneath.
- **Run it less often.** Moving the suite to nightly keeps the
  sensor but delays its reading until the change that broke it is
  weeks old and hard to find.

The meta-signal is the retry rate. A suite that needs retries to pass
is encoding assumptions it does not test.

## Response playbook

When an integration test fails:

1. **Classify the failure first.** Environment failure (missing
   service, wrong credentials) or boundary failure (wrong schema,
   wrong serialization, wrong timeout behavior)? The stack trace
   usually names the side, and the fix for one is useless for the
   other.
2. **Re-run once to separate flake from fact.** One failure in ten
   runs is a finding about a timing assumption, not noise to retry
   away. Two consecutive failures are the boundary.
3. **Fix the boundary, not the tolerance.** Raising a timeout to
   pass a slow dependency converts a reading into a liability that
   surfaces under real load. Fix the dependency or the call.
4. **Keep the real dependency where you can.** Every stub added to
   make the suite pass is an assumption promoted to untested. Prefer
   [contract tests](contract-tests.html) for the boundaries you must
   stub.

## What it cannot detect

Integration tests with mock dependencies don't test the real integration.
They test your assumptions about the real integration. [Contract
tests](contract-tests.html) are a stronger sensor for boundary assumptions.
