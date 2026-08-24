---
id: SO-010c
title: Onboarding Experiment
family: comprehension
family_num: '10'
oracle: low
oracle_note: onboarding time correlates with complexity
independence: high
independence_note: measured from external engineers
scope: module
latency: weeks
actionability: exploratory
actionability_note: shows where onboarding is slow
type: retrospective
stack_level: user-outcome
categories:
- Comprehension
see_also:
- SO-010
- SO-010b
- SO-010d
last_reviewed: '2026-08-24'
references:
- title: Onboarding vs. Diversity, Productivity and Quality — Empirical Study of the OpenStack Ecosystem
  year: 2021
  tier: II
  url: https://doi.org/10.1109/ICSE43902.2021.00097
  kind: paper
  authors: Armstrong Foundjem, Ellis E. Eghan, Bram Adams
  venue: ICSE 2021 (IEEE/ACM)
- title: GitHub's Engineering Team Has Moved to Codespaces
  year: 2021
  tier: III
  url: https://github.blog/engineering/infrastructure/githubs-engineering-team-moved-codespaces/
  kind: paper
  authors: Cory Wilkerson
  venue: GitHub Engineering Blog
---

How long does it take a competent engineer to safely modify this subsystem?
A sensor of *knowledge concentration* measured in onboarding time.

The onboarding experiment is the most direct sensor of epistemic
accessibility: give a competent engineer a task in an unfamiliar area and
measure how long it takes them to complete it safely. Long onboarding times
indicate implicit knowledge, missing documentation, or excessive coupling.

## In practice

The reading is a timed protocol record: one competent engineer, one
scoped task in an unfamiliar subsystem, phase-by-phase time and every
question asked.

```text
subject: senior engineer, 6 years, no prior payments experience
task: add retry with backoff to the webhook dispatcher, with tests
guard rails: reviewer on call, no production deploys

  phase                       time
  environment setup           1.5 days (build failed twice)
  locate the right module     0.5 days
  understand the call flow    1.5 days
  implement and test          0.5 days
  review and merge            1 day
  total                       5 days

  questions asked: 14 (9 of them to the same engineer)
```

Reading it well:

1. **Decompose where the time went.** Slow setup is a tooling problem;
   slow orientation is a comprehension problem; slow implementation is
   a design problem. The fix depends on which phase dominated.
2. **Count who got asked.** Nine questions to one person is a knowledge
   concentration finding independent of the total time.
3. **Compare against a control subsystem.** Absolute days mean little;
   the same engineer onboarding into a healthy module is the baseline.
4. **One subject is an anecdote.** Repeat the same task with the same
   protocol before believing any single run.

## How it gets gamed

- **Pick a trivial task.** "Add a log line" onboards fast anywhere; a
  task chosen for ease flatters the subsystem without testing it.
- **Pre-brief the subject.** Walking the subject through the system
  beforehand turns the measurement into a guided tour; the time then
  measures the guide, not the documentation.
- **Choose an insider.** A subject with prior system knowledge, or
  prior work with the same team, posts fast times for reasons that do
  not transfer to a genuine newcomer.
- **Measure first merge, not safe change.** Time to first merge can be
  trivially short while time to a *safe* change, the actual question,
  stays hidden.

The meta-signal is protocol consistency: task difficulty, subject
screening, and briefing rules held constant across runs. A result that
improved while the protocol quietly loosened is not an improvement.

## Response playbook

When an onboarding run reads badly:

1. **Classify the delay by phase.** Setup failures go to the team that
   owns the build; orientation time goes to documentation;
   comprehension time goes to the module's design.
2. **Turn every question into an artifact.** Each question the subject
   asked is a documentation gap; write the answer down where the
   subject looked for it, not in chat.
3. **Fix the environment first.** It is the cheapest fix and it
   compounds: every future onboarding and every CI run benefits.
4. **Convert the subject's notes into a runbook.** The person who just
   onboarded is briefly the best writer of onboarding docs; capture
   their path while it is fresh, then check it against the [drift
   audit](documentation-drift.html).
5. **Re-run the same task with the next subject.** The repeat run is
   the verification; if the second subject is still slow, the fix did
   not address the real blocker.

## What it cannot detect

Onboarding time conflates code complexity with many other factors: tooling,
build process, test infrastructure, team availability. A slow onboarding may
not reflect code quality at all. The methodology also matters:

- **Who** do you onboard? A junior measures documentation quality; a senior
  measures code legibility. The choice changes the signal.
- **Prior system knowledge** — an engineer who's seen a similar system
  elsewhere will onboard faster regardless of this system's clarity.
- **Noise** — a single onboarding is anecdote. You need repeated measures
  to get a signal, and repeated onboarding is expensive.

Treat the onboarding experiment as a structured protocol (same task, same
seniority level, same prior-knowledge screening), not a one-off timer.
