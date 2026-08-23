---
id: SO-002d
title: Snapshot Tests
family: behavioral
family_num: '02'
oracle: medium
oracle_note: 'change is detected, correctness is not'
independence: low
independence_note: 'same author creates the snapshot'
scope: function
latency: seconds
actionability: guiding
actionability_note: 'shows the diff between old and new output'
type: predictive
stack_level: behavioral-tests
categories:
- Behavioral
- Drift Detection
see_also:
- SO-002b
- SO-002c
- SO-003
last_reviewed: 2026-08-23
references:
- title: Jest snapshot
  kind: tool
  url: https://jestjs.io/docs/snapshot-testing
  description: Snapshot testing for JavaScript
- title: Vitest
  kind: tool
  url: https://vitest.dev
  description: Vite-native testing framework with snapshots
- title: instanbul
  kind: tool
  url: https://istanbul.js.org
  description: JavaScript code coverage
---

Did observable output change? Not "is it correct" but "did it change" — a
sensor for detecting *unintended drift* in externally observable artifacts.

Snapshot tests (also called golden master or approval tests) record a
canonical output and fail when it changes. They're particularly useful when
you don't know what the correct output is, but you know it shouldn't change
without intention.

## In practice

A reading is a diff between the recorded output and what the code
produces now:

```
FAIL src/invoice.test.js
  ● invoice renders with tax

    expect(received).toMatchSnapshot()

    - Snapshot  - 1
    + Received  + 1

        <div class="invoice">
    -     <span class="total">$108.00</span>
    +     <span class="total">$110.00</span>
        </div>

    1 snapshot failed. Run with `-u` to update.
```

Reading it well:

1. **Read the diff before you update it.** The update command makes
   the failure vanish by redefining correct as current. The diff is
   the only moment when a human judgment enters the loop.
2. **Small diffs can carry large meaning.** A currency symbol, a
   locale format, a sort order: one changed character can be the
   whole bug.
3. **State the reason before accepting a large diff.** Forty files
   moving after a shared component change can be legitimate, but only
   if you can say in one sentence why every file moved.
4. **Treat the snapshot file as the assertion.** It is committed
   code. Reviewing its changes in diff review is not ceremony; it is
   the test.

## How it gets gamed

The update command is the gaming surface:

- **Rubber-stamp the update.** Running the update flag without
  reading the diff redefines "correct" as "current" and turns the
  sensor into a formality. This is the dominant mode, because the
  command exists precisely to make red green.
- **Update in bulk.** Approving forty snapshots at once is a verdict
  about zero of them. Large batches should be split until each
  approval has a stated reason.
- **Shrink the snapshot.** Narrowing what gets snapshotted until the
  volatile part is excluded removes the drift the sensor was placed
  to catch.

The meta-signal is the ratio of updated snapshots to snapshot
failures. Near one, someone is approving unread diffs.

## Response playbook

When a snapshot fails:

1. **Read the diff before touching the update flag.** The diff is
   the only moment a human judgment enters the loop; the update
   command removes it.
2. **Decide intended versus accidental.** A change you meant to
   make is a snapshot that needs updating. A change you do not
   recognize is a behavioral reading, and the code is the suspect.
3. **State the reason for large diffs.** If forty files moved, name
   the shared cause in one sentence before approving. If you cannot,
   approve nothing.
4. **Commit the snapshot with the code change.** A snapshot updated
   in a separate commit hides the behavioral change inside a blob of
   test data.

## What it cannot detect

Snapshot tests can't tell you whether the *original* snapshot was correct.
They only detect *change*, not *correctness*. Also prone to "approve all"
fatigue when outputs are large.
