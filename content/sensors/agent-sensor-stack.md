---
id: SO-011
title: Agent Sensor Stack
family: ai-sensors
family_num: '11'
oracle: high
oracle_note: 'the combined stack is strong'
independence: high
independence_note: 'if producer and evaluator are separated'
scope: system
latency: varies
latency_note: 'varies by layer'
actionability: guiding
actionability_note: 'each layer tells the agent what failed'
type: predictive
type_note: 'predictive and retrospective, varies by layer'
stack_level: canary-shadow
categories:
- AI-Generated
- Agent Safety
see_also:
- SO-001
- SO-003
- SO-006
- SO-007
last_reviewed: 2026-08-23
references:
- title: 'Gender Shades: Intersectional Accuracy Disparities in Commercial Gender
    Classification'
  year: 2018
  tier: I
  url: http://proceedings.mlr.press/v81/buolamwini18a/buolamwini18a.pdf
  kind: paper
- title: 'Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift'
  year: 2019
  tier: I
  url: https://arxiv.org/pdf/1810.11953
  kind: paper
---

An agent should be surrounded by sensors. And crucially: the agent doesn't
get to declare success. The sensors declare success.

```
                 ┌──────────────┐
                 │   AGENT      │
                 │ writes code  │
                 └──────┬───────┘
                        │
          ┌─────────────┼──────────────┐
          ▼             ▼              ▼
      compiler        tests          linter
          │             │              │
          └─────────────┼──────────────┘
                        ▼
                  mutation test
                        │
                        ▼
                 integration test
                        │
                        ▼
                  canary sensor
                        │
                        ▼
                production events
                        │
                        ▼
                 outcome sensors
```

The agent sensor stack is the [confidence stack](atlas.html) applied to
AI-generated code: each layer is a gate the agent's output must pass before
it reaches production. The key principle is that the agent cannot self-certify
— [independence](framework.html) must be preserved at every layer.

## In practice

The stack cashes out as a pipeline where every layer is a gate the agent
cannot configure, skip, or grade:

1. The agent opens a pull request describing the change.
2. CI runs the [compiler](compiler.html), [type
   checker](type-checker.html), and [linter](linter.html). Any failure
   stops the pipeline before tests run.
3. The test suite runs, and the tests covering the change were not
   written by the agent that wrote the change.
4. [Mutation testing](mutation-testing.html) confirms the suite can
   actually fail.
5. A [second agent](second-agent-review.html) reviews the diff without
   access to the first agent's rationale.
6. Merge requires every gate plus an approval from outside the agent's
   session. The agent's own summary of its work is an input to no gate.

Two habits keep the reading honest:

- **Audit each gate's inputs, not just its verdicts.** A gate that
  consumes the agent's own tests, config, or summary is not
  independent, whatever it reports. See [producer-evaluator
  separation](producer-evaluator-separation.html).
- **The stack degrades one waiver at a time.** A skipped lint step
  here, a path exclusion there, and the stack still passes while
  testing less. Count how many layers an agent-touched change had to
  clear to merge, and notice when the number drops.

## Response playbook

When a layer fires on agent output:

1. **Stop the pipeline at the failing layer.** Do not let later gates
   run, and do not let the agent interpret its own failure as
   "warnings." A failed gate blocks; that is the entire arrangement.
2. **Feed the raw failure back to the agent.** Compiler errors, test
   names, and diff hunks go back as-is, not summarized by the agent's
   own assessment of what probably went wrong.
3. **Check whether the failing layer is compromised.** If the agent
   authored the tests or config that just passed or failed, fix the
   authorship first; rerunning a captured gate changes nothing.
4. **Re-run the stack from the first failing layer, not from the
   last.** A gate that passes after a retry may have been flaky; a
   stack re-run from the break shows whether the fix held downstream.
5. **Log every gate, verdict, and waiver.** The stack's history is the
   audit trail. A change that reached production with three waived
   layers is a finding, not an incident.

## What it cannot detect

The stack is only as strong as its weakest layer. If the agent writes the
tests (low independence), the test layer provides no real signal. See
[producer-evaluator separation](producer-evaluator-separation.html).
