---
id: SO-002
title: Contract Tests
family: behavioral
family_num: 2
oracle: high
oracle_note: a contract violation is a definite bug
independence: high
independence_note: consumer defines the contract
scope: service
latency: minutes
actionability: guiding
actionability_note: shows exactly which contract clause was violated
type: predictive
type_note: catches breaking changes before deployment
stack_level: integration-tests
categories:
- Behavioral
- Boundary Assumptions
see_also:
- SO-001
- SO-004
- change-family
- structural-family
last_reviewed: '2026-08-24'
references:
- title: 'I Depended on You and You Broke Me: An Empirical Study of Manifesting Breaking Changes in Client Packages'
  year: 2023
  tier: II
  url: https://arxiv.org/abs/2301.04563
  kind: paper
  authors: Suhaib Mujahid, Diego Elias Costa, Rabe Abdalkareem, Emad Shihab and others
  venue: ACM TOSEM
- title: 'Design, Monitoring, and Testing of Microservices Systems: The Practitioners'' Perspective'
  year: 2021
  tier: II
  url: https://arxiv.org/pdf/2108.03384
  kind: paper
  authors: Muhammad Waseem, Peng Liang, Mojtaba Shahin, Amleto Di Salle, Gastón Márquez
  venue: arXiv preprint, submitted to the Journal of Systems and Software
- authors: Ian Robinson
  title: Consumer-Driven Contracts
  year: 2007
  kind: paper
  tier: IV
- title: Pact
  url: https://pact.io
  kind: tool
  description: Consumer-driven contract testing
- title: Spring Cloud Contract
  kind: tool
  url: https://spring.io/projects/spring-cloud-contract
  description: Contract testing for Spring/JVM
- title: Postman
  kind: tool
  url: https://www.postman.com
  description: API testing and contract validation
scope_note: between services, at their boundaries
---

Does service A continue satisfying the assumptions of service B? Contract
tests are a sensor of *boundary assumptions* — the implicit agreements
between independent components about what the interface between them
promises.

## Contracts measure boundary assumptions

A *contract* is a specification of what one component promises to provide
and what another component is allowed to assume. Contract tests verify that
both sides of the boundary continue to honor these promises as the system
evolves.

```
# Consumer-driven contract
Service B (consumer) defines:
  "I expect GET /users/{id} to return
   { id: int, name: string, active: bool }"

Service A (provider) must satisfy:
  its response matches this shape
  the field types are correct
  the endpoint exists and responds
```

The sensor detects *breaking changes* — when a provider modifies its API in
a way that violates the assumptions its consumers depend on. This is
particularly powerful in microservice architectures where independent teams
deploy independently.

> Contracts measure boundary assumptions. Types measure a particular class
> of structural inconsistency. Contract tests are the boundary-level version
> of what type checkers are at the module level: both enforce structural
> promises, but at different scopes and different feedback latencies.

## In practice

A reading is a pact verification failure that names the broken clause
and the consumer it belongs to:

```
Verifying a pact between Orders (consumer) and Billing (provider)

  A request for invoice 42
    GET /invoices/42
      returns a response which
        has status code 200
        includes headers
          "Content-Type" with value "application/json"  FAILED
            actual value: "text/html"
        has a matching body                             FAILED
          $.amount: expected number, got string

2 interactions, 2 failures
```

Reading it well:

1. **Read the clause, not just the red.** Status, header, and body
   failures have different owners and different fixes. The clause
   names which promise broke.
2. **The failure belongs to the change, not the expectation.** The
   consumer stated its assumption first; the provider moved. The fix
   direction is usually to hold the provider to the promise, not to
   relax the expectation.
3. **A passing pact is one-directional evidence.** It says the
   provider honors the recorded expectations. It does not say the
   expectations are complete: a consumer that never wrote a pact is
   a gap the sensor cannot see.

## How it gets gamed

- **Delete or weaken the pact.** Removing an expectation the
  provider now violates turns red to green without fixing the
  provider. The consumer still holds the old assumption, so the
  breakage moves from the report to production.
- **Verify against a stub.** Running the provider side of a pact
  against a mock instead of the real service passes the check and
  tests nothing.
- **Let pacts go stale.** A pact not re-verified after a provider
  change is an assumption wearing a check mark.

The meta-signal is the pact count per consumer over time. A pact file
that shrinks after a failure is the sensor being overridden.

## Response playbook

When a contract test fails:

1. **Read the broken clause.** Status, header, and body failures
   have different owners. The clause names which promise broke and
   which consumer depends on it.
2. **Assume the provider is wrong until shown otherwise.** The
   consumer stated its assumption before the provider changed. The
   default fix is restoring the promise, not relaxing the pact.
3. **If the consumer is wrong, change both sides together.** Update
   the pact and the consumer in the same change, so the window where
   neither matches is zero.
4. **Check the other consumers.** A broken clause usually breaks
   every consumer that holds it. The report names one; the pact
   broker lists the rest.

## What it cannot detect

Contract tests verify the *shape* of communication, not its *meaning*. A
response that has the right fields and types but contains wrong values will
pass a contract test. They also cannot detect
[integration failures](catalog.html#behavioral) that emerge from the
*interaction* of correct components producing incorrect emergent behavior.
