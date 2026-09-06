---
order: 20
kind: starting-point
title: "You inherited a codebase nobody explains"
where: >-
  The team that wrote it is gone. It builds, the tests pass, and you are
  about to change something without knowing what else it touches or why it
  was written that way.
have:
  - compiler
  - example-based-tests
steps:
  - sensor: hotspot-analysis
    closes: [risk-concentrated]
    why: >-
      Compiling and passing say nothing about where the trouble sits. One
      run over twelve months of git history ranks the modules that are both
      complex and constantly changed, which is where your first change is
      most likely to hurt and where the rest of this list should point.
  - sensor: dependency-graph
    closes: [structure-decayed]
    why: >-
      The hotspot says where to look; the graph says what a change there
      reaches. Fan-in on the hot modules and the cycle list are the two
      numbers you need before touching anything, and an import rule that
      refuses an edge is the cheapest reading of them.
  - sensor: decision-provenance
    closes: [unexplained]
    why: >-
      You now know where the coupling is and still not why. Pick one line
      in the top hotspot that looks wrong and trace it with git blame and
      git log -S; how far back the reason survives is the reading, and it
      costs twenty minutes per question.
  - sensor: snapshot-tests
    closes: [unintended-change]
    why: >-
      You are about to change code you do not understand, and the inherited
      tests encode the previous team's intentions. Recording the current
      output of the hot module freezes behaviour you cannot yet judge, so the
      diff tells you when a change touched something you did not mean to.
  - sensor: mutation-testing
    closes: [unasserted-execution]
    why: >-
      The snapshots guard what you froze; the inherited suite is the rest of
      your net, and passing only says it ran. One mutation run on the top
      hotspot tells you whether those tests would notice a wrong answer, and
      its no-coverage column tells you which code they never saw at all.
  - sensor: smoke-tests
    closes: [does-not-run-where-deployed]
    why: >-
      Every step so far happens before deploy. Your first release is the
      first time the runbook is followed by someone who did not write it,
      and four requests against the fresh deploy find the missing config
      value in minutes rather than from a user.
skip:
  - sensor: onboarding-experiment
    reason: >-
      It closes the same doubt as decision provenance, and you are already
      the subject. A single run with no control subsystem is an anecdote,
      and the anecdote is your own week.
  - sensor: change-coupling
    reason: >-
      Also closes the coupling doubt, and finds pairs the dependency graph
      cannot see. Run it after the graph, because the finding is a pair that
      changes together with no import edge between them, and you need the
      edges first to know which pairs those are.
---
