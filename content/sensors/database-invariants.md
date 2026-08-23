---
id: SO-004b
title: Database Invariants
family: invariants
family_num: '04'
oracle: high
independence: high
scope: system
latency: minutes
actionability: guiding
type: retrospective
stack_level: production-behavior
categories:
- Invariants
- Referential Integrity
- Runtime Sensors
see_also:
- SO-004
- SO-004c
- SO-006
last_reviewed: 2026-08-23
references:
- title: 'Detecting Data Errors: Where are we and what needs to be done?'
  year: 2016
  tier: I
  url: https://www.vldb.org/pvldb/vol9/p993-abedjan.pdf
  kind: paper
- title: 'Jepsen: MongoDB 4.2.6'
  year: 2020
  tier: II
  url: https://jepsen.io/analyses/mongodb-4.2.6
  kind: paper
- title: DB constraints
  kind: tool
  url: https://www.postgresql.org/docs/current/ddl-constraints.html
  description: Database-level CHECK/FOREIGN KEY constraints
- title: CHECK constraints
  kind: tool
  url: https://www.postgresql.org/docs/current/ddl-constraints.html#ddl-constraints-check-constraints
  description: SQL CHECK constraints
- title: foreign keys
  kind: tool
  url: https://www.postgresql.org/docs/current/tutorial-fk.html
  description: Database referential integrity constraints
- title: pg_constraint
  kind: tool
  url: https://www.postgresql.org/docs/current/catalog-pg-constraint.html
  description: PostgreSQL constraint catalog
---

Every foreign key refers to an existing object. Every request has exactly
one request_id. `created_at <= updated_at`. These are sensors of
*referential integrity* — structural invariants that the database enforces.

Database invariants operate at a different level than [runtime
invariants](runtime-invariants.html): they're checked by the database
engine itself, not by querying the event stream. This gives them high oracle
strength but limits them to properties the schema can express.

## Sensor properties

| Property | Value |
|----------|-------|
| Oracle strength | High — constraint violation is definitive |
| Independence | High — database enforces, not the application |
| Scope | System-level |
| Feedback latency | Minutes |
| Actionability | Guiding — shows which constraint was violated |
| Type | Retrospective |

## What it cannot detect

Only properties expressible as database constraints. Business rules
("a successful payment implies an order eventually becomes paid") require
[runtime invariants](runtime-invariants.html) checked against [event
streams](observability-events.html).
