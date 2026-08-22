---
id: SO-004b
title: Database Invariants
family: invariants
family_num: "04"
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
