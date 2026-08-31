---
id: SO-009
title: Revert Rate
family: evolution
family_num: 09
oracle: medium
oracle_note: reversion correlates with problems
independence: high
independence_note: computed from git history
scope: module
latency: days
latency_note: days to weeks
actionability: exploratory
actionability_note: shows the pattern, you investigate
type: retrospective
stack_level: user-outcome
categories:
- Evolution
- Black-Box Sensors
- Maintainability
see_also:
- SO-009b
- SO-009c
- SO-009d
- SO-007e
- SO-015b
references:
- title: git log
  kind: tool
  url: https://git-scm.com/docs/git-log
  description: Git commit history
- title: git-quick-stats
  kind: tool
  url: https://github.com/arzzen/git-quick-stats
  description: Git history analysis script
- title: CodeScene
  kind: tool
  url: https://codescene.com
  description: Code analysis predicting technical debt from behavioral code
---

How often does this area get reverted? A *black-box sensor* of
maintainability — you don't need to understand `FooManagerFactoryImpl`, you
can observe: 27 changes in six months, 8 reverts, 4 incidents, touched by
11 teams. That's a signal.

Revert rate is a retrospective sensor: it tells you that changes in this
area have historically been unreliable, without reading a single line of
code. High revert rate is a leading indicator of complexity, poor testing,
or misunderstood requirements.

## In practice

A revert rate reading comes out of git history: per module or directory,
the count of changes landed versus the count of those changes returned.
Computed over the trailing six months:

```
git log --oneline --grep='^Revert' -- src/billing | wc -l

area            changes   reverts   revert rate
src/billing        27        8         30%
src/checkout       41        2          5%
src/search         15        0          0%
```

The reading is comparative: 30% next to 5% is the signal, not 30% by
itself. Habits that make it usable:

1. **Compare areas, not absolute numbers.** Revert rate only means
   something against a peer: this module reverts three times more often
   than the neighboring one. Cross-area comparison is the actual
   sensor.
2. **Normalize by change volume.** A module with two changes and one
   revert is not the same reading as one with fifty changes and
   twenty-five reverts, even at the same rate. Look at both columns.
3. **Read reverts alongside incidents.** A revert that rolled back a
   broken deploy is a different event than a revert of a merge
   conflict. The count alone does not say which; the incident record
   does.
4. **Watch the window.** Revert rate over days measures merge hygiene;
   over months it measures design quality. Pick the window that
   matches the question before comparing numbers.

## How it gets gamed

Revert rate is computed from git history, and history can be shaped:

- **Batching work to dilute the denominator.** Shipping many small
   unrelated changes alongside a risky one spreads the revert cost
   across a larger change count, lowering the rate without lowering
   the risk. The area looks stable; the risky change is still risky.
- **Fixing forward instead of reverting.** A broken change gets
   patched in place rather than reverted, so the failure never enters
   the count. The rate reads clean while the same class of mistake
   keeps happening. Sometimes fixing forward is right; when it becomes
   policy, the sensor goes blind.
- **Rebranding reverts.** Squashing the revert into a commit titled
   "adjustments" or "cleanup" removes the keyword the counter greps
   for. The event survives; the record does not.

The meta-signal is the ratio of fix-forward commits to reverts in the
same area. If reverts fall while fix-forwards rise, the work is being
re-labeled, not repaired.

## Response playbook

When a module's revert rate climbs or a change keeps bouncing:

1. **Read the reverted diffs, not the rate.** Pull the revert commits
   and their targets. The reasons cluster: schema assumptions, missing
   tests, unclear ownership. Act on the cluster, not the number.
2. **Shrink the change size in that area.** High revert rate usually
   means changes are bigger than the module's test coverage can
   protect. Split work until individual changes are small enough to
   revert cleanly.
3. **Add the missing sensor before the next change.** If reverts keep
   citing the same failure class, install the check that would have
   caught it: a [type checker](type-checker.html) pass, an integration
   test, a fitness function for the boundary being crossed.
4. **Pair the area for one cycle.** When a module reverts repeatedly,
   the next change through it gets a second set of eyes at review time.
   This is temporary; the goal is finding what the area knows that the
   author does not.

## What it cannot detect

Revert rate can't tell you *why* changes are reverted. It identifies
where attention is needed, not what the fix is. Also misses problems that
were fixed forward rather than reverted.
