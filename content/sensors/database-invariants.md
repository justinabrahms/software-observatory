---
id: SO-004b
title: Database Invariants
family: invariants
family_num: '04'
oracle: high
oracle_note: constraint violation is definitive
independence: high
independence_note: database enforces, not the application
scope: system
latency: minutes
actionability: guiding
actionability_note: shows which constraint was violated
type: retrospective
stack_level: production-behavior
categories:
- Invariants
- Production Sensors
see_also:
- SO-004
- SO-004c
- SO-006
references:
- title: 'Detecting Data Errors: Where are we and what needs to be done?'
  year: 2016
  tier: I
  url: https://www.vldb.org/pvldb/vol9/p993-abedjan.pdf
  kind: publication
  authors: Ziawasch Abedjan, Xu Chu, Dong Deng, Raul Castro Fernandez, Ihab F. Ilyas, Mourad Ouzzani, Paolo Papotti, Michael Stonebraker, Nan Tang
  venue: PVLDB 9(12)
- title: 'Jepsen: MongoDB 4.2.6'
  year: 2020
  tier: II
  url: https://jepsen.io/analyses/mongodb-4.2.6
  kind: publication
  authors: Kyle Kingsbury (Jepsen)
  venue: jepsen.io analyses
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

## In practice

A reading is a constraint violation exactly as the database reports it,
with the constraint name, the offending statement, and the values:

```
ERROR:  insert or update on table "orders" violates foreign key
        constraint "orders_customer_id_fkey"
DETAIL:  Key (customer_id)=(88213) is not present in table "customers".
STATEMENT:  INSERT INTO orders (customer_id, total) VALUES (88213, 4120);
```

Three habits for reading it well:

- **The constraint name is the invariant.** `orders_customer_id_fkey`
  says which relationship broke. Name constraints deliberately so the
  error line reads like a sentence about the domain.
- **One violation usually means many.** The database stops at the
  first row it cannot reconcile, so a single error on a batch write
  implies a systematic cause: a missing join, a deleted parent, an
  out-of-order migration.
- **Know which checks are deferred.** Constraints added `NOT VALID`,
  or enforced by triggers rather than the engine, are cheaper to run
  and easier to lose. Know which of your invariants are
  engine-enforced and which are merely scheduled.

## How it gets gamed

The database cannot be argued with, but the constraints can be edited:

- **Disable instead of fix.** Dropping `NOT VALID` enforcement,
  deleting a trigger, or loosening a CHECK turns violations into
  silence. The data is no worse than before; the sensor is just gone.
- **Clean up before the check.** Batch jobs reconcile the tables
  shortly before the audit query runs, so the reading is of the
  cleanup, not of the system. Point-in-time checks are harder to
  scrub than scheduled ones.
- **Move the write around the schema.** Raw SQL, an admin endpoint,
  or a manual migration that skips the validated path keeps the
  constraints pristine while data goes in unexamined.
- **Let dirty data grandfather itself.** Existing violations freeze
  the rule in place, because enabling the constraint now would fail.
  Every skipped fix compounds into a migration too expensive to run.

The meta-signal is the constraint diff. Schema migrations that remove
or relax constraints are deletions of a sensor, and deserve review the
way deleting a test would.

## Response playbook

When a constraint violation fires:

1. **Stop the write that triggered it.** A failing `INSERT` or
   `UPDATE` means the application is trying to put the database in an
   impossible state. Roll back the transaction; do not retry the same
   write.
2. **Read the constraint name as the diagnosis.**
   `orders_customer_id_fkey` tells you which relationship broke. Find
   the code path that issued the statement; the database has already
   told you the what, so spend the budget on the why.
3. **Check for dirty data already written.** The violation surfaced on
   one row, but the same cause may have written many. Run the
   constraint as a `SELECT` across the table before assuming the
   failure is isolated.
4. **Fix the application, not the constraint.** Dropping or relaxing
   the constraint to unblock a deploy is the gaming path. If the
   constraint is genuinely wrong, change it in a migration with a
   named owner, not under incident pressure.
5. **Add the failing case as a test.** The write that violated the
   constraint is a free specification. Encode it as a regression test
   so the next version of the application fails in CI, not in
   production.

## What it cannot detect

Only properties expressible as database constraints. Business rules
("a successful payment implies an order eventually becomes paid") require
[runtime invariants](runtime-invariants.html) checked against [event
streams](observability-events.html).
